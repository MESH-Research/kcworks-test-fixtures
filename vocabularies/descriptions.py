# Part of KCWorks Test Fixtures
# Copyright (C) 2023-2025, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Vocabulary pytest fixtures for descriptions."""

import pytest

from tests.fixtures.vocabularies.rebuild_helpers import ensure_shared_vocabulary_type

TYPE_ID = "descriptiontypes"
PID_TYPE = "dty"


DESCRIPTION_TYPES = [
    {
        "id": "methods",
        "title": {"en": "Methods"},
        "props": {"datacite": "Methods"},
    },
    {
        "id": "abstract",
        "title": {"en": "Abstract"},
        "props": {"datacite": "Abstract"},
    },
    {
        "id": "other",
        "title": {"en": "Other"},
        "props": {"datacite": "Other"},
    },
]


def ensure_description_types_vocabulary(refresh: bool = True) -> int:
    """Ensure the description type vocabulary records exist.

    Returns:
        The number of new description type entries created.
    """
    return ensure_shared_vocabulary_type(
        type_id=TYPE_ID,
        pid_type=PID_TYPE,
        rows=DESCRIPTION_TYPES,
        refresh=refresh,
    )


@pytest.fixture(scope="module")
def description_type_v(bootstrap_vocabularies) -> None:
    """Fixture to ensure description type vocabulary records are available."""
    return None
