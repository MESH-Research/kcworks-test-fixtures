# Part of KCWorks Test Fixtures
# Copyright (C) 2023-2025, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource type vocabulary fixtures."""

import copy

import pytest

from tests.fixtures.vocabularies.rebuild_helpers import (
    ensure_shared_vocabulary_type,
    rebuild_shared_vocabulary_type,
)

TYPE_ID = "resourcetypes"
PID_TYPE = "rsrct"


RESOURCE_TYPES = [
    {
        "id": "textDocument",
        "props": {
            "csl": "text",
            "datacite_general": "Text",
            "datacite_type": "",
            "openaire_resourceType": "21",
            "openaire_type": "article",
            "eurepo": "info:eu-repo/semantics/other",
            "schema.org": "https://schema.org/Text",
            "subtype": "",
            "type": "textDocument",
        },
        "icon": "file alt outline",
        "title": {"en": "Text Document"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
    },
    {
        "id": "textDocument-interviewTranscript",
        "props": {
            "csl": "interview",
            "datacite_general": "Text",
            "datacite_type": "Interview",
            "openaire_resourceType": "21",
            "openaire_type": "article",
            "eurepo": "info:eu-repo/semantics/other",
            "schema.org": "https://schema.org/Interview",
            "subtype": "textDocument-interviewTranscript",
            "type": "textDocument",
        },
        "icon": "file alt outline",
        "title": {"en": "Interview Transcript"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
    },
    {
        "id": "textDocument-bookSection",
        "props": {
            "csl": "book-section",
            "datacite_general": "Book Section",
            "datacite_type": "",
            "openaire_resourceType": "21",
            "openaire_type": "article",
            "eurepo": "info:eu-repo/semantics/other",
            "schema.org": "https://schema.org/BookSection",
            "subtype": "textDocument-bookSection",
            "type": "textDocument",
        },
        "icon": "file alt outline",
        "title": {"en": "Book Section"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
    },
    {
        "id": "textDocument-conferenceProceeding",
        "props": {
            "csl": "conference-paper",
            "datacite_general": "Conference Proceeding",
            "datacite_type": "",
            "openaire_resourceType": "21",
            "openaire_type": "article",
            "eurepo": "info:eu-repo/semantics/other",
            "schema.org": "https://schema.org/ConferenceProceeding",
            "subtype": "textDocument-conferenceProceeding",
            "type": "textDocument",
        },
        "icon": "file alt outline",
        "title": {"en": "Conference Proceeding"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
    },
    {
        "id": "textDocument-thesis",
        "props": {
            "csl": "thesis",
            "datacite_general": "Thesis",
            "datacite_type": "",
            "openaire_resourceType": "21",
            "openaire_type": "article",
            "eurepo": "info:eu-repo/semantics/other",
            "schema.org": "https://schema.org/Thesis",
            "subtype": "textDocument-thesis",
            "type": "textDocument",
        },
        "icon": "file alt outline",
        "title": {"en": "Thesis"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
    },
    {
        "id": "textDocument-whitePaper",
        "props": {
            "csl": "report",
            "datacite_general": "Report",
            "datacite_type": "",
            "openaire_resourceType": "21",
            "openaire_type": "article",
            "eurepo": "info:eu-repo/semantics/other",
            "schema.org": "https://schema.org/Report",
            "subtype": "textDocument-whitePaper",
            "type": "textDocument",
        },
        "icon": "file alt outline",
        "title": {"en": "White Paper"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
    },
    {
        "id": "textDocument-journalArticle",
        "icon": "table",
        "props": {
            "csl": "article-journal",
            "datacite_general": "Journal Article",
            "datacite_type": "Article",
            "openaire_resourceType": "21",
            "openaire_type": "article",
            "eurepo": "info:eu-repo/semantics/other",
            "schema.org": "https://schema.org/Article",
            "subtype": "textDocument-journalArticle",
            "type": "textDocument",
        },
        "title": {"en": "Journal Article"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
    },
    {
        "id": "textDocument-review",
        "icon": "thumbs up outline",
        "props": {
            "coar": "review",
            "coar_type": "c_efa0",
            "csl": "review",
            "datacite_general": "Journal Article",
            "datacite_type": "Review",
            "eurepo": "info:eu-repo/semantics/review",
            "schema.org": "https://schema.org/Review",
            "subtype": "textDocument-review",
            "type": "textDocument",
        },
        "title": {"en": "Review"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
    },
    {
        "id": "dataset",
        "icon": "table",
        "props": {
            "csl": "dataset",
            "datacite_general": "Dataset",
            "datacite_type": "",
            "openaire_resourceType": "21",
            "openaire_type": "dataset",
            "eurepo": "info:eu-repo/semantics/other",
            "schema.org": "https://schema.org/Dataset",
            "subtype": "",
            "type": "dataset",
        },
        "title": {"en": "Dataset"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
    },
    {
        "id": "image",
        "props": {
            "csl": "figure",
            "datacite_general": "Image",
            "datacite_type": "",
            "openaire_resourceType": "25",
            "openaire_type": "dataset",
            "eurepo": "info:eu-repo/semantic/other",
            "schema.org": "https://schema.org/ImageObject",
            "subtype": "",
            "type": "image",
        },
        "icon": "chart bar outline",
        "title": {"en": "Image"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
    },
    {
        "id": "image-photograph",
        "props": {
            "csl": "graphic",
            "datacite_general": "Image",
            "datacite_type": "Photo",
            "openaire_resourceType": "25",
            "openaire_type": "dataset",
            "eurepo": "info:eu-repo/semantic/other",
            "schema.org": "https://schema.org/Photograph",
            "subtype": "image-photograph",
            "type": "image",
        },
        "icon": "chart bar outline",
        "title": {"en": "Photo"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
    },
    {
        "id": "textDocument-book",
        "icon": "book",
        "title": {"en": "Book"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
        "props": {
            "csl": "book",
            "datacite_general": "Book",
            "datacite_type": "",
            "openaire_resourceType": "21",
            "openaire_type": "article",
            "eurepo": "info:eu-repo/semantics/other",
            "schema.org": "https://schema.org/Book",
            "subtype": "textDocument-book",
            "type": "textDocument",
        },
    },
    {
        "id": "presentation-other",
        "icon": "file powerpoint",
        "title": {"en": "Other Presentation"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
        "props": {
            "csl": "presentation",
            "datacite_general": "Presentation",
            "datacite_type": "",
            "openaire_resourceType": "21",
            "openaire_type": "article",
            "eurepo": "info:eu-repo/semantics/other",
            "schema.org": "https://schema.org/Presentation",
            "subtype": "presentation-other",
            "type": "presentation",
        },
    },
    {
        "id": "other",
        "icon": "file",
        "title": {"en": "Other"},
        "tags": ["depositable", "linkable"],
        "type": "resourcetypes",
        "props": {
            "csl": "other",
            "datacite_general": "Other",
            "datacite_type": "",
            "openaire_resourceType": "21",
            "openaire_type": "article",
            "eurepo": "info:eu-repo/semantics/other",
            "schema.org": "https://schema.org/Other",
            "subtype": "",
            "type": "other",
        },
    },
]


@pytest.fixture(scope="module")
def resource_types() -> list[dict]:
    """Fixture to create the resource type vocabulary.

    Returns:
        list[dict]: A deep copy of the RESOURCE_TYPES list.
    """
    return copy.deepcopy(RESOURCE_TYPES)


def ensure_resource_types_vocabulary(refresh: bool = True) -> int:
    """Ensure the resource type vocabulary records exist.

    Returns:
        The number of new resource type entries created.
    """
    return ensure_shared_vocabulary_type(
        type_id=TYPE_ID,
        pid_type=PID_TYPE,
        rows=copy.deepcopy(RESOURCE_TYPES),
        refresh=refresh,
    )


@pytest.fixture(scope="module")
def resource_type_v(bootstrap_vocabularies) -> None:
    """Fixture to ensure resource type vocabulary records are available."""
    return None


@pytest.fixture(scope="function")
def reindex_resource_types(running_app) -> None:
    """Ensure resource type vocabulary search is populated from Postgres."""
    rebuild_shared_vocabulary_type(
        type_id=TYPE_ID,
        pid_type=PID_TYPE,
        refresh=True,
    )
