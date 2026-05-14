# Part of kcworks-test-fixtures
# Copyright (C) 2023-2026, MESH Research
#
# kcworks-test-fixtures is free software; you can redistribute and/or
# modify it under the terms of the MIT License; see LICENSE file for more details.

"""Test helpers for rebuilding vocabularies."""

from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_resources.proxies import current_service_registry
from invenio_search.proxies import current_search
from invenio_vocabularies.proxies import current_service as vocabulary_service
from invenio_vocabularies.records.api import Vocabulary
from invenio_vocabularies.records.models import VocabularyMetadata, VocabularyType
from sqlalchemy.exc import NoResultFound


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

    return new_entries


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
    if not Vocabulary.index.exists():
        list(current_search.create(index_list=["vocabularies"]))

    results = vocabulary_service.read_all(
        system_identity,
        fields=["id"],
        type=type_id,
        cache=False,
    )

    if results.total > 0:
        return 0

    type_ids = [type_id]
    if pid_type:
        type_ids.append(pid_type)

    db_records = VocabularyMetadata.query.filter(
        VocabularyMetadata.json.op("->")("type").op("->>")("id").in_(type_ids)
    ).all()

    if not db_records:
        return 0

    for db_record in db_records:
        record = Vocabulary.get_record(db_record.id)
        vocabulary_service.indexer.index(record, arguments={})

    if refresh:
        Vocabulary.index.refresh()

    return len(db_records)


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
    service = current_service_registry.get(service_name)

    if not record_cls.index.exists():
        list(current_search.create(index_list=[index_alias]))

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
        # Missing index / broken alias / empty search state -> rebuild below.
        pass

    service.rebuild_index(system_identity)

    if refresh:
        record_cls.index.refresh()

    return db_count
