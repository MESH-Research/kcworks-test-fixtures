# Part of KCWorks Test Fixtures
# Copyright (C) 2023-2025, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Vocabulary pytest fixtures for funding and awards."""

import pytest
from invenio_vocabularies.contrib.awards.api import Award
from invenio_vocabularies.contrib.funders.api import Funder

from tests.fixtures.vocabularies.rebuild_helpers import ensure_service_vocabulary

FUNDER_IDS = [
    "00k4n6c31",
    "00k4n6c32",
    "00k4n6c33",
    "00k4n6c34",
    "00k4n6c35",
    "00k4n6c36",
]

AWARD_IDS = [
    "00k4n6c31::755021",
    "00k4n6c32::755022",
    "00k4n6c33::755023",
    "00k4n6c34::755024",
    "00k4n6c35::755025",
    "00k4n6c36::755026",
]

FUNDER_DATA = [
    {
        "id": funder,
        "identifiers": [
            {
                "identifier": funder,
                "scheme": "ofr",
            },
        ],
        "name": f"Funder {funder}",
        "title": {
            "en": f"Funder {funder}",
            "fr": f"Fournisseur {funder}",
        },
        "country": "BE",
    }
    for funder in FUNDER_IDS
]

AWARD_DATA = [
    {
        "id": award,
        "identifiers": [
            {
                "identifier": f"https://sandbox.kcworks.org/{award}",
                "scheme": "url",
            },
        ],
        "number": award.split("::")[1],
        "title": {
            "en": f"Award {award.split('::')[1]}",
        },
        "funder": {"id": award.split("::")[0]},
        "acronym": "HIT-CF",
        "program": "H2020",
    }
    for award in AWARD_IDS
]


def ensure_funders_vocabulary(refresh: bool = True) -> int:
    """Ensure the funders vocabulary records exist.

    Returns:
        The number of new funder entries created.
    """
    return ensure_service_vocabulary(
        service_name="funders",
        rows=FUNDER_DATA,
        record_cls=Funder,
        refresh=refresh,
    )


def ensure_awards_vocabulary(refresh: bool = True) -> int:
    """Ensure the awards vocabulary records exist.

    Returns:
        The number of new award entries created.
    """
    ensure_funders_vocabulary(refresh=refresh)
    return ensure_service_vocabulary(
        service_name="awards",
        rows=AWARD_DATA,
        record_cls=Award,
        refresh=refresh,
    )


@pytest.fixture(scope="module")
def funders_v(bootstrap_vocabularies) -> None:
    """Fixture to ensure funder vocabulary records are available."""
    return None


@pytest.fixture(scope="module")
def awards_v(bootstrap_vocabularies, funders_v: None) -> None:
    """Fixture to ensure award vocabulary records are available."""
    return None
