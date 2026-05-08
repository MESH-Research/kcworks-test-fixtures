# Part of invenio-remote-user-data-kcworks
# Copyright (C) 2023-2026, MESH Research
#
# invenio-remote-user-data-kcworks is free software; you can redistribute and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test fixtures related to the names vocabulary."""

from pathlib import Path

from invenio_i18n import lazy_gettext as _
from invenio_rdm_records.config import always_valid
from invenio_vocabularies.config import (
    VOCABULARIES_NAMES_SCHEMES as _UPSTREAM_NAMES_SCHEMES,
)

# Detect if we're running from a generic context (e.g., stats-dashboard)
# If the file path contains "invenio-stats-dashboard", exclude KCWorks custom schemes
_IS_GENERIC_CONTEXT = "invenio-stats-dashboard" in str(Path(__file__).resolve())


if not _IS_GENERIC_CONTEXT:
    VOCABULARIES_NAMES_SCHEMES = {
        **_UPSTREAM_NAMES_SCHEMES,
        "kc_username": {
            "label": _("KC member"),
            "validator": always_valid,
            "datacite": "Other",
        },
    }
    """Names vocabulary allowed identifier schemes (KCWorks extensions)."""

SAMPLE_NAME_RESULT = {
    "id": "gihctester",
    "created": "2026-05-06T18:02:22.432478+00:00",
    "updated": "2026-05-06T18:02:22.438609+00:00",
    "links": {"self": "http://localhost/api/names/gihctester"},
    "revision_id": 3,
    "tags": ["kcworks-user"],
    "internal_id": None,
    "name": "Hc, Ghost",
    "given_name": "Ghost",
    "family_name": "Hc",
    "identifiers": [
        {"identifier": "gihctester", "scheme": "kc_username"},
        {"identifier": "0000-0002-1825-0097", "scheme": "orcid"},
    ],
    "affiliations": [],
    "props": {
        "kcworks_user_id": "2",
        "name_parts": {"first": "Ghost", "last": "Hc"},
        "display_name": "Hc, Ghost",
        "family_token": "hc",
        "family_part_tokens": ["hc"],
        "family_phonetic_tokens": ["HK"],
    },
}
