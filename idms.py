# Part of KCWorks Test Fixtures
# Copyright (C) 2026, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Text fixture related to remote IDMS actions."""

import inspect
import time

import pytest
from flask import current_app


def _set_test_cookie(client, name: str, value: str) -> None:
    """Set a cookie on a Flask test client across Werkzeug versions.

    Werkzeug <= 2.2 uses ``set_cookie(server_name, key, value, ...)`` while
    Werkzeug >= 2.3/3.x uses ``set_cookie(key, value, *, domain=...)``. The
    KCWorks test suite currently runs on Werkzeug 2.2, but we detect the
    signature so the helper keeps working if the pin changes.
    """
    params = list(inspect.signature(client.set_cookie).parameters)
    if params and params[0] == "server_name":
        # The default test client request host is ``localhost``; the cookie's
        # server_name must match it so the cookie is sent with the request.
        client.set_cookie("localhost", name, value)
    else:
        client.set_cookie(name, value)


@pytest.fixture(scope="function")
def bypass_silent_sso_redirect(running_app, client):
    """Skip the silent-SSO before_request redirect for anonymous UI requests.

    invenio-remote-user-data-kcworks registers a ``before_request`` handler that
    redirects anonymous UI requests to the Profiles silent-login broker (a 302)
    whenever its retry cookie is absent or expired. Tests that exercise UI routes
    with an anonymous ``client`` would otherwise receive that redirect instead of
    the target view. Seeding the retry cookie with a fresh timestamp makes
    ``BrokerHelpers.ready_for_login_broker_check()`` return ``False`` so the hook
    is a no-op.

    Returns:
        FlaskClient: The same test client, with the SSO retry cookie set.
    """
    cookie_name = running_app.app.config.get(
        "SSO_BROKER_RETRY_COOKIE_NAME", "_sso_checked"
    )
    _set_test_cookie(client, cookie_name, str(int(time.time())))
    return client


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
