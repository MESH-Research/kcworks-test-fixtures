# Part of KCWorks Test Fixtures
# Copyright (C) 2023-2025, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Vocabulary pytest fixtures for licenses."""

import pytest

from tests.fixtures.vocabularies.rebuild_helpers import ensure_shared_vocabulary_type

TYPE_ID = "licenses"
PID_TYPE = "lic"


# List of license data dictionaries
LICENSE_DATA = [
    {
        "id": "arr",
        "props": {
            "url": "https://arr.org/licenses/all-rights-reserved",
            "scheme": "spdx",
            "osi_approved": "",
        },
        "title": {"en": "All Rights Reserved"},
        "description": {"en": "All Rights Reserved"},
    },
    {
        "id": "cc-by-4.0",
        "props": {
            "url": "https://creativecommons.org/licenses/by/4.0/legalcode",
            "scheme": "spdx",
            "osi_approved": "",
        },
        "title": {"en": "Creative Commons Attribution 4.0 International"},
        "description": {
            "en": (
                "The Creative Commons Attribution license allows"
                " re-distribution and re-use of a licensed work on"
                " the condition that the creator is appropriately credited."
            )
        },
    },
    {
        "id": "cc-by-nc-4.0",
        "props": {
            "url": "https://creativecommons.org/licenses/by-nc/4.0/legalcode",
            "scheme": "spdx",
            "osi_approved": "",
        },
        "title": {"en": "Creative Commons Attribution-NonCommercial 4.0 International"},
        "description": {
            "en": (
                "The Creative Commons Attribution-NonCommercial license allows"
                " re-distribution and re-use of a licensed work on"
                " the condition that the creator is appropriately credited."
            )
        },
    },
    {
        "id": "cc-by-nc-nd-4.0",
        "props": {
            "url": "https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode",
            "scheme": "spdx",
            "osi_approved": "",
        },
        "title": {
            "en": (
                "Creative Commons Attribution-NonCommercial-"
                "NoDerivatives 4.0 International"
            )
        },
        "description": {
            "en": (
                "The Creative Commons Attribution-NonCommercial"
                "-NoDerivatives license allows"
                " re-distribution and re-use of a licensed work on"
                " the condition that the creator is appropriately credited."
            )
        },
    },
    {
        "id": "cc-by-sa-4.0",
        "props": {
            "url": "https://creativecommons.org/licenses/by-sa/4.0/legalcode",
            "scheme": "spdx",
            "osi_approved": "",
        },
        "title": {"en": "Creative Commons Attribution-ShareAlike 4.0 International"},
        "description": {
            "en": (
                "The Creative Commons Attribution-ShareAlike license allows"
                " re-distribution and re-use of a licensed work on"
                " the condition that the creator is appropriately credited."
            )
        },
    },
]


def ensure_licenses_vocabulary(refresh: bool = True) -> int:
    """Ensure the licenses vocabulary records exist.

    Returns:
        The number of new license entries created.
    """
    return ensure_shared_vocabulary_type(
        type_id=TYPE_ID,
        pid_type=PID_TYPE,
        rows=[
            {**license_data, "tags": ["recommended", "all"]}
            for license_data in LICENSE_DATA
        ],
        refresh=refresh,
    )


@pytest.fixture(scope="module")
def licenses_v(app) -> None:
    """Fixture to create the licenses vocabulary records."""
    ensure_licenses_vocabulary()
