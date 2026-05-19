# Part of KCWorks Test Fixtures
# Copyright (C) 2026, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Text fixture related to remote IDMS actions."""

import pytest
from flask import current_app


@pytest.fixture
def mock_logout_signal_receiver(requests_mock):
    """Factory fixture to generate mock receiver for a user.

    Returns:
        Callable: Function to mock the signal receiver.
    """

    def mock_receiver(username: str | None = None):
        """Mock the receiver URL for the KC central logout."""
        if not username:
            username = "john_doe"
        success_body = {
            "message": "Action successfully triggered.",
            "data": {
                "user": {"user": username, "url": f"/profiles/{username}/"},
                "user_agent": "Mozilla/5.0 ...",
                "app": ["Profiles", "Works", "WordPress"],
            },
        }
        requests_mock.post(
            f"{current_app.config.get('IDMS_BASE_API_URL')}actions/logout/",
            json=success_body,
        )

    return mock_receiver
