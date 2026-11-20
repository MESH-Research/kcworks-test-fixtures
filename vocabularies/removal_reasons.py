# Part of KCWorks Test Fixtures
# Copyright (C) 2023-2026, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Vocabulary pytest fixtures for record removal reasons."""

import pytest

from tests.fixtures.vocabularies.rebuild_helpers import (
    ensure_shared_vocabulary_type,
    rebuild_shared_vocabulary_type,
)

TYPE_ID = "removalreasons"
PID_TYPE = "rem"

# Subset of invenio-rdm-records fixtures/data/vocabularies/removal_reasons.yaml
removal_reason_data = [
    {
        "id": "spam",
        "title": {"en": "Spam"},
    },
    {
        "id": "test-record",
        "title": {"en": "Test upload of a record"},
    },
    {
        "id": "duplicate",
        "title": {"en": "Duplicate of another record"},
    },
]


def ensure_removal_reasons_vocabulary(refresh: bool = True) -> int:
    """Ensure the removal-reason vocabulary type and records exist.

    Args:
        refresh: Whether to refresh the search index after creating new items.

    Returns:
        The number of new entries created.
    """
    return ensure_shared_vocabulary_type(
        type_id=TYPE_ID,
        pid_type=PID_TYPE,
        rows=removal_reason_data,
        refresh=refresh,
    )


@pytest.fixture(scope="module")
def removal_reason_v(bootstrap_vocabularies) -> None:
    """Fixture to ensure removal-reason vocabulary records are available."""
    return None


def rebuild_removal_reasons_vocabulary(refresh: bool = True) -> int:
    """Rebuild the removalreasons index from DB-backed records.

    Args:
        refresh: Whether to refresh the vocabulary index after rebuilding.

    Returns:
        The number of rebuilt vocabulary entries.
    """
    return rebuild_shared_vocabulary_type(
        type_id=TYPE_ID, pid_type=PID_TYPE, refresh=refresh
    )


@pytest.fixture(scope="module")
def rebuild_removal_reasons_search(bootstrap_vocabularies) -> None:
    """Fixture to rebuild removal-reason vocabulary search from DB."""
    rebuild_removal_reasons_vocabulary()
