# Part of KCWorks Test Fixtures
# Copyright (C) 2024-2025, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Fixtures for mail-related testing.

The root ``test_config`` sets ``MAIL_SUPPRESS_SEND=True`` so the suite does not
hit SparkPost unless a test opts in. Mail integration tests should request both
the pytest-invenio ``mailbox`` fixture (captures outgoing messages) and
``enable_mail_sending`` (temporarily sets ``MAIL_SUPPRESS_SEND=False``).
"""

import os
from typing import Any

import pytest

test_config_mail: dict[str, Any] = {
    "MAIL_SUPPRESS_SEND": True,
    "MAIL_SERVER": "smtp.sparkpostmail.com",
    "MAIL_PORT": 587,
    "MAIL_USE_TLS": True,
    "MAIL_USE_SSL": False,
    "MAIL_USERNAME": os.getenv("SPARKPOST_USERNAME", "test-unused"),
    "MAIL_PASSWORD": os.getenv("SPARKPOST_API_KEY", "test-unused"),
    "MAIL_DEFAULT_SENDER": os.getenv("INVENIO_ADMIN_EMAIL", "test@example.com"),
}


@pytest.fixture
def enable_mail_sending(running_app):
    """Temporarily enable mail sending for a test.

    Use together with the pytest-invenio ``mailbox`` fixture when asserting on
    outgoing email. Restores ``MAIL_SUPPRESS_SEND`` after the test.

    Args:
        running_app: Invenio test app fixture from pytest-invenio.
    """
    original_value = running_app.app.config["MAIL_SUPPRESS_SEND"]
    running_app.app.config["MAIL_SUPPRESS_SEND"] = False

    yield  # This is where the test runs

    running_app.app.config["MAIL_SUPPRESS_SEND"] = original_value
