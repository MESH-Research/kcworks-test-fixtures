# Part of KCWorks Test Fixtures
# Copyright (C) 2023-2025, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Vocabulary pytest fixtures for date types."""

import pytest
from invenio_search.proxies import current_search_client
from invenio_vocabularies.proxies import current_service as vocabulary_service
from invenio_vocabularies.records.api import Vocabulary
from invenio_vocabularies.records.models import VocabularyMetadata

from tests.fixtures.vocabularies.rebuild_helpers import ensure_shared_vocabulary_type

TYPE_ID = "datetypes"
PID_TYPE = "dat"


date_type_data = [
    {
        "id": "issued",
        "title": {"en": "Issued", "de": "Veröffentlicht"},
        "props": {"datacite": "Issued", "marc": "iss"},
    },
    {
        "id": "available",
        "title": {"en": "Available"},
        "props": {"datacite": "Available", "marc": "ava"},
    },
    {
        "id": "accepted",
        "title": {"en": "Accepted"},
        "props": {"datacite": "Accepted", "marc": "acc"},
    },
    {
        "id": "other",
        "title": {"en": "Other"},
        "props": {"datacite": "Other", "marc": "oth"},
    },
]


def ensure_date_types_vocabulary(refresh: bool = True) -> int:
    """Ensure the date type vocabulary records exist.

    Returns:
        The number of new date type entries created.
    """
    return ensure_shared_vocabulary_type(
        type_id=TYPE_ID,
        pid_type=PID_TYPE,
        rows=date_type_data,
        refresh=refresh,
    )


@pytest.fixture(scope="module")
def date_type_v(bootstrap_vocabularies) -> None:
    """Fixture to ensure date type vocabulary records are available."""
    return None


@pytest.fixture(scope="function")
def reindex_date_types(running_app) -> None:
    """Ensure vocabulary search indices exist and are populated.

    This method checks if vocabulary indices are missing or empty and
    recreates/reindexes them if needed. This is necessary because in
    some cases the vocabulary indices are destroyed by the search_clear fixture
    between tests, but the records are still in the database.
    """
    search_client = current_search_client
    index_name = "vocabularies"

    if not search_client.indices.exists(index=index_name):
        Vocabulary.index.create()

    # First check if the vocabulary type 'datetypes' exists
    type_search = search_client.search(
        index=index_name,
        body={"query": {"term": {"id": "datetypes"}}, "size": 1},
    )

    # Then check if it has vocabulary term records
    terms_search = search_client.search(
        index=index_name,
        body={"query": {"term": {"type": "datetypes"}}, "size": 1},
    )

    if (
        type_search["hits"]["total"]["value"] == 0
        or terms_search["hits"]["total"]["value"] == 0
    ):
        db_records = VocabularyMetadata.query.filter(
            VocabularyMetadata.json
            .op("->")("type")
            .op("->>")("id")
            .in_(["datetypes", "dat"])
        ).all()

        if db_records:
            for db_record in db_records:
                record = Vocabulary.get_record(db_record.id)
                vocabulary_service.indexer.index(record, arguments={})
            Vocabulary.index.refresh()
