# Part of KCWorks Test Fixtures
# Copyright (C) 2023-2025, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Vocabulary pytest fixtures for roles."""

import pytest

from tests.fixtures.vocabularies.rebuild_helpers import ensure_shared_vocabulary_type

CREATORS_TYPE_ID = "creatorsroles"
CREATORS_PID_TYPE = "crr"
CONTRIBUTORS_TYPE_ID = "contributorsroles"
CONTRIBUTORS_PID_TYPE = "cor"

creatibutor_roles = [
    {
        "id": "author",
        "props": {"datacite": "Author"},
        "title": {"en": "Author"},
    },
    {
        "id": "editor",
        "props": {"datacite": "Editor"},
        "title": {"en": "Editor"},
    },
    {
        "id": "datamanager",
        "props": {"datacite": "DataManager"},
        "title": {"en": "Data manager"},
    },
    {
        "id": "projectmanager",
        "props": {"datacite": "ProjectManager"},
        "title": {"en": "Project manager"},
    },
    {
        "id": "translator",
        "props": {"datacite": "Translator"},
        "title": {"en": "Translator"},
    },
    {
        "id": "other",
        "props": {"datacite": "Other", "marc": "oth"},
        "title": {"en": "Other"},
    },
]


def ensure_creators_roles_vocabulary(refresh: bool = True) -> int:
    """Ensure the creator role vocabulary records exist.

    Returns:
        The number of new creator role entries created.
    """
    return ensure_shared_vocabulary_type(
        type_id=CREATORS_TYPE_ID,
        pid_type=CREATORS_PID_TYPE,
        rows=creatibutor_roles,
        refresh=refresh,
    )


@pytest.fixture(scope="module")
def creators_role_v(bootstrap_vocabularies) -> None:
    """Fixture to ensure creator role vocabulary records are available."""
    return None


def ensure_contributors_roles_vocabulary(refresh: bool = True) -> int:
    """Ensure the contributor role vocabulary records exist.

    Returns:
        The number of new contributor role entries created.
    """
    return ensure_shared_vocabulary_type(
        type_id=CONTRIBUTORS_TYPE_ID,
        pid_type=CONTRIBUTORS_PID_TYPE,
        rows=creatibutor_roles,
        refresh=refresh,
    )


@pytest.fixture(scope="module")
def contributors_role_v(bootstrap_vocabularies) -> None:
    """Fixture to ensure contributor role vocabulary records are available."""
    return None
