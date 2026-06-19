# Part of KCWorks Test Fixtures
# Copyright (C) 2023-2026, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Vocabulary pytest fixtures for affiliations."""

import pytest
from invenio_vocabularies.contrib.affiliations.api import Affiliation

from tests.fixtures.vocabularies.rebuild_helpers import (
    ensure_service_vocabulary,
    rebuild_service_vocabulary,
)

affiliation_data = [
    {
        "id": "cern",
        "name": "CERN",
        "acronym": "CERN",
        "identifiers": [
            {
                "scheme": "ror",
                "identifier": "01ggx4157",
            },
        ],
    },
    {
        "id": "03rmrcq20",
        "name": "University of British Columbia",
        "acronym": "UBC",
        "identifiers": [
            {
                "scheme": "ror",
                "identifier": "03rmrcq20",
            },
        ],
    },
    {
        "id": "013v4ng57",
        "name": "San Francisco Public Library",
        "acronym": "SFPL",
        "identifiers": [
            {
                "scheme": "ror",
                "identifier": "013v4ng57",
            },
        ],
    },
]


def ensure_affiliations_vocabulary(refresh: bool = True) -> int:
    """Ensure the affiliation vocabulary records exist.

    Idempotent. This will not conflict with or modify existing entries for the same
    vocabulary items.

    Returns:
        The number of new entries added.
    """
    return ensure_service_vocabulary(
        service_name="affiliations",
        rows=affiliation_data,
        record_cls=Affiliation,
        refresh=refresh,
    )


@pytest.fixture(scope="module")
def affiliations_v(bootstrap_vocabularies) -> None:
    """Fixture function to ensure affiliation vocabulary records are available."""
    return None


def rebuild_affiliations_vocabulary(refresh: bool = True) -> int:
    """Rebuild the affiliations index from DB-backed records.

    Args:
        refresh: Whether to refresh the affiliation index after rebuilding.

    Returns:
        int: The number of rebuilt search entries.
    """
    return rebuild_service_vocabulary(
        service_name="affiliations",
        record_cls=Affiliation,
        index_alias="affiliations",
        refresh=refresh,
    )


@pytest.fixture(scope="module")
def rebuild_affiliations_v(app) -> None:
    """Fixture function to create the affiliation vocabulary records."""
    with app.app_context():
        rebuild_affiliations_vocabulary()
