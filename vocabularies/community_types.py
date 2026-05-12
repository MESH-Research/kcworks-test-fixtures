# Part of KCWorks Test Fixtures
# Copyright (C) 2023-2025, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Vocabulary pytest fixtures for community types."""

import pytest

from tests.fixtures.vocabularies.rebuild_helpers import (
    ensure_shared_vocabulary_type,
    rebuild_shared_vocabulary_type,
)

TYPE_ID = "communitytypes"
PID_TYPE = "comtyp"

community_type_data = [
    {
        "id": "organization",
        "title": {"en": "Organization"},
        "type": "communitytypes",
    },
    {
        "id": "event",
        "title": {"en": "Event"},
        "type": "communitytypes",
    },
    {
        "id": "topic",
        "title": {"en": "Topic"},
        "type": "communitytypes",
    },
    {
        "id": "project",
        "title": {"en": "Project"},
        "type": "communitytypes",
    },
    {
        "id": "group",
        "title": {"en": "Group"},
        "type": "communitytypes",
    },
    {
        "id": "commons",
        "title": {"en": "Commons"},
        "type": "communitytypes",
    },
]


def ensure_community_types_vocabulary(refresh: bool = True) -> int:
    """Ensure the community type vocabulary type and records exist.

    Args:
        refresh: Whether to refresh the search index after creating new items.

    Returns:
        The number of new entries created.
    """
    return ensure_shared_vocabulary_type(
        type_id=TYPE_ID,
        pid_type=PID_TYPE,
        rows=community_type_data,
        refresh=refresh,
    )


@pytest.fixture(scope="module")
def community_type_v(app) -> None:
    """Fixture to create the community type vocabulary records."""
    ensure_community_types_vocabulary()


def rebuild_community_types_vocabulary(refresh: bool = True) -> int:
    """Rebuild the community_types index from DB-backed records.

    Args:
        refresh: Whether to refresh the affiliation index after rebuilding.

    Returns:
        int: The number of rebuilt vocabulary entries.
    """
    return rebuild_shared_vocabulary_type(
        type_id=TYPE_ID, pid_type=PID_TYPE, refresh=refresh
    )


@pytest.fixture(scope="module")
def rebuild_community_types_v() -> None:
    """Fixture to rebuild the community_types index from DB-backed records."""
    rebuild_community_types_vocabulary()
