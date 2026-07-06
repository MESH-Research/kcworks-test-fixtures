# Part of kcworks-test-fixtures
# Copyright (C) 2023-2026, MESH Research
#
# kcworks-test-fixtures is free software; you can redistribute and/or
# modify it under the terms of the MIT License; see LICENSE file for more details.

"""Test helpers for rebuilding vocabularies."""

import inspect

from invenio_access.permissions import system_identity
from invenio_cache import current_cache
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_resources.proxies import current_service_registry
from invenio_search.proxies import current_search, current_search_client
from invenio_vocabularies.proxies import current_service as vocabulary_service
from invenio_vocabularies.records.api import Vocabulary
from invenio_vocabularies.records.models import VocabularyMetadata, VocabularyType
from sqlalchemy.exc import NoResultFound


def _shared_vocabulary_type_ids(type_id: str, pid_type: str | None) -> list[str]:
    """Return DB JSON type ids used to locate shared vocabulary rows."""
    type_ids = [type_id]
    if pid_type:
        type_ids.append(pid_type)
    return type_ids


def _shared_vocabulary_db_query(type_id: str, pid_type: str | None):
    """Return a query for DB rows belonging to one shared vocabulary type."""
    type_ids = _shared_vocabulary_type_ids(type_id, pid_type)
    return VocabularyMetadata.query.filter(
        VocabularyMetadata.json.op("->")("type").op("->>")("id").in_(type_ids)
    )


def _shared_vocabulary_search_total(type_id: str) -> int | None:
    """Return the number of search hits for a vocabulary type, if queryable.

    Returns:
        Document count for the type in the vocabularies index, or ``None`` if
        the count query fails.
    """
    try:
        response = current_search_client.count(
            index=Vocabulary.index.search_alias,
            body={"query": {"term": {"type.id": type_id}}},
        )
    except Exception:
        return None
    return response["count"]


def _clear_vocabulary_read_all_cache(type_id: str) -> None:
    """Drop cached ``read_all`` responses for one vocabulary type.

    ``VocabularyService.read_all`` stores serialized OpenSearch responses in
    Redis via Flask-Caching (``current_cache``). Logical keys look like
    ``{type_id}_{extra_filter}_{field-field-...}`` — for example
    ``languages__id`` or ``resourcetypes_<filter>_id-props.datacite``.

    Flask-Caching prefixes those with ``CACHE_KEY_PREFIX`` (typically
    ``cache::``). Keys are discovered with ``SCAN`` on the Redis backend, then
    removed through ``current_cache.unlink`` using the logical key names.
    """
    try:
        backend = current_cache.cache
    except (AttributeError, RuntimeError):
        return

    redis_client = getattr(backend, "_read_client", None)
    if redis_client is None:
        return

    key_prefix = getattr(backend, "key_prefix", None) or ""
    pattern = f"{key_prefix}{type_id}_*"
    logical_keys: list[str] = []
    for redis_key in redis_client.scan_iter(match=pattern, count=100):
        key = redis_key.decode() if isinstance(redis_key, bytes) else redis_key
        if key_prefix and key.startswith(key_prefix):
            logical_keys.append(key[len(key_prefix) :])

    if logical_keys:
        current_cache.unlink(*logical_keys)


def _clear_get_cached_vocab_type(vocabulary_type: str) -> None:
    """Drop in-process facet label cache entries for one vocabulary type.

    ``VocabularyLabels`` (used for record search facets such as ``languages`` and
    ``resourcetypes``) caches individual ``read_many`` lookups via
    ``get_cached_vocab``. Cache keys are ``(service_id, type, fields, id_)``;
    only entries whose ``type`` matches ``vocabulary_type`` are removed.

    Subjects facets do not use this cache (``SubjectsLabels`` is a pass-through).
    """
    from invenio_vocabularies.services.facets import get_cached_vocab

    try:
        nonlocals = inspect.getclosurevars(get_cached_vocab).nonlocals
        cache = nonlocals.get("cache")
        cache_lock = nonlocals.get("cache_lock")
        if not isinstance(cache, dict) or cache_lock is None:
            get_cached_vocab.cache_clear()
            return

        stale_keys = [
            key for key in cache if len(key) >= 2 and key[1] == vocabulary_type
        ]
        with cache_lock:
            for key in stale_keys:
                cache.pop(key, None)
    except (TypeError, ValueError, AttributeError):
        get_cached_vocab.cache_clear()


def clear_vocabulary_label_caches(type_id: str) -> None:
    """Clear cached vocabulary labels for one vocabulary type.

    Two layers are involved:

    * **In-process facet cache** — ``get_cached_vocab`` entries for
      ``VocabularyLabels("…")`` (e.g. ``languages``, ``resourcetypes``).
      Only entries for ``type_id`` are dropped.
    * **Redis ``read_all`` cache** — serializer and UI lookups keyed as
      ``{type_id}_…`` (e.g. ``resourcetypes_<filter>_id-props.datacite``).
      Cleared via a scoped Redis ``SCAN``, not a full cache flush.

    Large vocabs such as ``subjects`` are not touched unless ``type_id`` names
    them explicitly.

    Args:
        type_id: Vocabulary type id whose label caches should be cleared.
    """
    _clear_get_cached_vocab_type(type_id)
    _clear_vocabulary_read_all_cache(type_id)


def _sync_shared_vocabulary_search_index(
    type_id: str,
    pid_type: str | None,
    refresh: bool = True,
) -> int:
    """Reindex shared vocabulary rows from Postgres when search is stale.

    Returns:
        Number of DB-backed records reindexed, or 0 if search already matches DB.
    """
    if not Vocabulary.index.exists():
        list(current_search.create(index_list=["vocabularies"]))

    query = _shared_vocabulary_db_query(type_id, pid_type)
    db_count = query.count()
    if db_count == 0:
        return 0

    search_total = _shared_vocabulary_search_total(type_id)
    if search_total is None or search_total < db_count:
        for db_record in query.all():
            record = Vocabulary.get_record(db_record.id)
            vocabulary_service.indexer.index(record, arguments={})

        if refresh:
            Vocabulary.index.refresh()

        clear_vocabulary_label_caches(type_id)
        return db_count

    clear_vocabulary_label_caches(type_id)
    return 0


def ensure_shared_vocabulary_type(
    type_id: str,
    pid_type: str,
    rows: list[dict],
    refresh: bool = True,
) -> int:
    """Ensure a shared vocabulary type and its records exist.

    Args:
        type_id: Vocabulary type id, e.g. `"communitytypes"`.
        pid_type: PID type id for the shared vocabulary type.
        rows: Vocabulary records to ensure.
        refresh: Whether to refresh the shared vocabulary index.

    Returns:
        Number of new records created.
    """
    if VocabularyType.query.filter_by(id=type_id).one_or_none() is None:
        vocabulary_service.create_type(system_identity, type_id, pid_type)

    new_entries = 0
    for row in rows:
        try:
            vocabulary_service.read(system_identity, (type_id, row["id"]))
        except PIDDoesNotExistError:
            vocabulary_service.create(system_identity, {**row, "type": type_id})
            new_entries += 1

    if refresh and new_entries > 0:
        Vocabulary.index.refresh()

    _sync_shared_vocabulary_search_index(type_id, pid_type, refresh=refresh)
    return new_entries


def ensure_service_vocabulary(
    service_name: str,
    rows: list[dict],
    record_cls: type,
    refresh: bool = True,
) -> int:
    """Ensure a dedicated service-backed vocabulary exists.

    Args:
        service_name: Service registry key, e.g. `"affiliations"`.
        rows: Vocabulary records to ensure.
        record_cls: Record API class with an index to refresh.
        refresh: Whether to refresh the service index after new records.

    Returns:
        Number of new records created.
    """
    service = current_service_registry.get(service_name)

    new_entries = 0
    for row in rows:
        try:
            service.read(system_identity, row["id"])
        except (PIDDoesNotExistError, NoResultFound):
            service.create(system_identity, row)
            new_entries += 1

    if refresh and new_entries > 0:
        record_cls.index.refresh()

    _sync_service_vocabulary_search_index(service_name, record_cls, refresh=refresh)
    return new_entries


def _sync_service_vocabulary_search_index(
    service_name: str,
    record_cls: type,
    index_alias: str | None = None,
    refresh: bool = True,
) -> int:
    """Reindex a dedicated service vocabulary from Postgres when search is stale.

    Returns:
        Number of DB-backed records reindexed, or 0 if search already matches DB.
    """
    service = current_service_registry.get(service_name)
    alias = index_alias or service_name

    if not record_cls.index.exists():
        list(current_search.create(index_list=[alias]))

    model_cls = record_cls.model_cls
    db_count = (
        model_cls.query.filter(model_cls.is_deleted == False).count()  # noqa: E712
    )
    if db_count == 0:
        return 0

    try:
        results = service.search(system_identity, params={"size": 1})
        if results.total >= db_count:
            return 0
    except Exception:
        pass

    service.rebuild_index(system_identity)

    if refresh:
        record_cls.index.refresh()

    return db_count


def rebuild_shared_vocabulary_type(
    type_id: str,
    pid_type: str | None = None,
    refresh: bool = True,
) -> int:
    """Reindex one vocabulary type from the shared vocabularies index.

    Args:
        type_id: Vocabulary type id, e.g. `"communitytypes"`.
        pid_type: Optional pid type id, e.g. `"comtyp"`.
        refresh: Whether to refresh the index after rebuilding.

    Returns:
        Number of DB-backed records reindexed.
    """
    return _sync_shared_vocabulary_search_index(type_id, pid_type, refresh=refresh)


def rebuild_service_vocabulary(
    service_name: str,
    record_cls,
    index_alias: str,
    refresh: bool = True,
) -> int:
    """Reindex one dedicated service-backed vocabulary.

    Args:
        service_name: Service registry key, e.g. `"affiliations"`.
        record_cls: Record API class, e.g. `Affiliation`.
        index_alias: Logical alias name for `current_search.create(...)`.
        refresh: Whether to refresh the index after rebuilding.

    Returns:
        Number of DB-backed records reindexed.
    """
    return _sync_service_vocabulary_search_index(
        service_name,
        record_cls,
        index_alias=index_alias,
        refresh=refresh,
    )
