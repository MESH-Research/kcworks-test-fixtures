# Part of kcworks-test-fixtures
# Copyright (C) 2026, MESH Research
#
# kcworks-test-fixtures is free software; you can redistribute and/or
# modify it under the terms of the MIT License; see LICENSE file for more details.

"""Site and remote-service URL defaults for tests."""

from __future__ import annotations

import os
from typing import Any

idms_base = "https://profile.hcommons-dev.org/api/v1/"

test_config_urls: dict[str, Any] = {
    "SITE_API_URL": os.environ.get("INVENIO_SITE_API_URL", "http://localhost/api"),
    "SITE_UI_URL": os.environ.get("INVENIO_SITE_UI_URL", "http://localhost"),
    "IDMS_BASE_API_URL": idms_base,
    "SSO_BROKER_LOGIN_URL": "https://profile.hcommons-dev.org/login/",
    "SSO_BROKER_SILENT_LOGIN_URL": (
        "https://profile.hcommons-dev.org/broker/silent-login/"
    ),
    "SSO_BROKER_VERIFY_NONCE_URL": (
        "https://profile.hcommons-dev.org/broker/verify-nonce/"
    ),
}
test_config_urls["OAISERVER_ID_PREFIX"] = test_config_urls["SITE_UI_URL"]
