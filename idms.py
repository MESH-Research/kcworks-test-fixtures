# Part of KCWorks Test Fixtures
# Copyright (C) 2026, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test fixtures related to remote IDMS actions."""

import inspect
import os
import time
from typing import Any

import pytest
from flask import current_app, g, request
from flask_principal import Identity, identity_changed
from invenio_accounts.models import User
from invenio_accounts.proxies import current_datastore
from invenio_oauth2server.proxies import current_oauth2server
from pydantic import BaseModel, ConfigDict

from invenio_remote_user_data_kcworks.types.profiles_api import (
    APIResponse,
    Meta,
    Profile,
    SubData,
)
from invenio_remote_user_data_kcworks.utils.broker import extract_bearer_token
from invenio_remote_user_data_kcworks.utils.static_token import (
    resolve_static_token_route,
)


class _AccessTokenStandIn(BaseModel):
    """Minimal stand-in for OAuth `Token`; static-token flow only uses `scopes`."""

    scopes: set[str]


class _OAuthStandIn(BaseModel):
    """Minimal stand-in for `request.oauth` after static bearer auth."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    user: User
    access_token: _AccessTokenStandIn


def minimal_profile(**overrides: Any) -> Profile:
    """Return a valid minimal Profiles API `Profile` payload."""
    payload = {
        "username": "myuser",
        "name": "My User",
        "email": "myuser@example.org",
        "first_name": "My",
        "last_name": "User",
        "institutional_affiliation": None,
        "orcid": None,
        "academic_interests": [],
        "groups": [],
        "avatar": None,
        "url": None,
        "is_superadmin": False,
    }
    payload.update(overrides)
    return Profile(**payload)


def minimal_api_response(
    sub: str,
    *,
    authorized: bool = True,
    profile: Profile | None = None,
    **profile_overrides: Any,
) -> APIResponse:
    """Return a valid minimal `subs` endpoint response."""
    if profile is None:
        profile = minimal_profile(**profile_overrides)
    elif profile_overrides:
        profile = Profile(**{**profile.model_dump(mode="python"), **profile_overrides})

    return APIResponse(
        data=[SubData(sub=sub, profile=profile)],
        meta=Meta(authorized=authorized),
        next=None,
        previous=None,
    )


def empty_api_response(*, authorized: bool = True) -> APIResponse:
    """Return a valid empty `subs` endpoint response."""
    return APIResponse(
        data=[],
        meta=Meta(authorized=authorized),
        next=None,
        previous=None,
    )


def _idms_static_api_token_before_request() -> None:
    """If path + Bearer match `STATIC_API_TOKEN_ROUTES`, impersonate configured user.

    Mirrors KCWorks `site/kcworks/ext.py`; installed from `tests.conftest` for API
    tests that use `create_api` without the site `api_finalize_app` hook.
    """
    if getattr(request, "oauth_verify_has_run", False):
        return

    binding = resolve_static_token_route(
        request.path,
        current_app.config.get("STATIC_API_TOKEN_ROUTES") or {},
        current_app.config,
    )
    if binding is None or binding.user_id is None:
        return
    static_token = os.environ.get(binding.token_env)
    if not static_token:
        return
    try:
        token = extract_bearer_token(request.headers.get("Authorization") or "")
    except ValueError:
        return
    if token != static_token:
        return

    user = current_datastore.find_user(id=binding.user_id)
    if not user or not user.active:
        return

    # Match invenio_oauth2server's oauth path so require_api_auth does not
    # treat the static bearer as a JWT (ACCOUNTS_JWT_ENABLE).
    user.login_via_oauth2 = True
    g._login_user = user
    identity_changed.send(
        current_app._get_current_object(),
        identity=Identity(user.id),  # type: ignore[arg-type]
    )
    scopes = {
        sid
        for sid, _ in current_oauth2server.scope_choices(exclude_internal=False)
    }
    request.oauth = _OAuthStandIn(  # type: ignore[attr-defined]
        user=user,
        access_token=_AccessTokenStandIn(scopes=scopes),
    )
    request.skip_csrf_check = True  # type: ignore[attr-defined]
    request.oauth_verify_has_run = True  # type: ignore[attr-defined]


def register_idms_static_api_token_before_request(app) -> None:
    """Prepend the IDMS static-token handler when `STATIC_API_TOKEN_ROUTES` is set."""
    routes_map = app.config.get("STATIC_API_TOKEN_ROUTES") or {}
    if not routes_map:
        return
    funcs = app.before_request_funcs.get(None, [])
    if _idms_static_api_token_before_request in funcs:
        return
    app.before_request_funcs[None] = [_idms_static_api_token_before_request] + funcs


def _set_test_cookie(client, name: str, value: str) -> None:
    """Set a cookie on a Flask test client across Werkzeug versions.

    Werkzeug <= 2.2 uses `set_cookie(server_name, key, value, ...)` while
    Werkzeug >= 2.3/3.x uses `set_cookie(key, value, *, domain=...)`. The
    KCWorks test suite currently runs on Werkzeug 2.2, but we detect the
    signature so the helper keeps working if the pin changes.
    """
    params = list(inspect.signature(client.set_cookie).parameters)
    if params and params[0] == "server_name":
        # The default test client request host is `localhost`; the cookie's
        # server_name must match it so the cookie is sent with the request.
        client.set_cookie("localhost", name, value)
    else:
        client.set_cookie(name, value)


@pytest.fixture(scope="function")
def bypass_silent_sso_redirect(running_app, client):
    """Skip the silent-SSO before_request redirect for anonymous UI requests.

    invenio-remote-user-data-kcworks registers a `before_request` handler that
    redirects anonymous UI requests to the Profiles silent-login broker (a 302)
    whenever its retry cookie is absent or expired. Tests that exercise UI routes
    with an anonymous `client` would otherwise receive that redirect instead of
    the target view. Seeding the retry cookie with a fresh timestamp makes
    `BrokerHelpers.ready_for_login_broker_check()` return `False` so the hook
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


# Mirrors `site/kcworks/config/auth.py`. Opt-in fixtures install this map when
# a test needs inbound static-token auth (parent suites may already load it
# from invenio.cfg; package suites often do not).
_SPLIT_STATIC_API_TOKEN_ROUTES = {
    "/api/webhooks/user_data_update": {
        "token_env": "COMMONS_PROFILES_API_TOKEN",
        "user_id_config": "STATIC_API_TOKEN_USER_ID_PROFILES",
    },
    "/api/webhooks/users/update": {
        "token_env": "COMMONS_PROFILES_API_TOKEN",
        "user_id_config": "STATIC_API_TOKEN_USER_ID_PROFILES",
    },
    "/api/webhooks/users/logout": {
        "token_env": "COMMONS_SSO_LOGOUT_API_TOKEN",
        "user_id_config": "STATIC_API_TOKEN_USER_ID_SSO",
    },
    "/webhooks/user_data_update": {
        "token_env": "COMMONS_PROFILES_API_TOKEN",
        "user_id_config": "STATIC_API_TOKEN_USER_ID_PROFILES",
    },
    "/webhooks/users/update": {
        "token_env": "COMMONS_PROFILES_API_TOKEN",
        "user_id_config": "STATIC_API_TOKEN_USER_ID_PROFILES",
    },
    "/webhooks/users/logout": {
        "token_env": "COMMONS_SSO_LOGOUT_API_TOKEN",
        "user_id_config": "STATIC_API_TOKEN_USER_ID_SSO",
    },
}


@pytest.fixture(scope="function")
def idms_static_api_principals(
    app,
    admin_roles,
    monkeypatch,
) -> dict[str, str]:
    """Enable inbound static-token auth with distinct Profiles and SSO bearers.

    Looks up the durable `svc-commons-profiles` / `svc-commons-sso` accounts
    seeded by package ensure (via `admin_roles`), then:

    - Keeps distinct `COMMONS_PROFILES_API_TOKEN` /
      `COMMONS_SSO_LOGOUT_API_TOKEN` values
    - Points `STATIC_API_TOKEN_USER_ID_*` at those users
    - Installs the split `STATIC_API_TOKEN_ROUTES` map and before-request hook

    Returns:
        Dict with `profiles_token` and `sso_token` bearer strings (no
        `Bearer` prefix). Prefer `idms_static_api_auth` /
        `idms_sso_static_api_auth` for request headers.
    """
    from tests.fixtures.env_defaults import (
        PYTEST_DEFAULT_COMMONS_PROFILES_API_TOKEN,
        PYTEST_DEFAULT_COMMONS_SSO_LOGOUT_API_TOKEN,
    )
    from tests.fixtures.users import get_durable_service_user

    profiles_token = (
        os.getenv("COMMONS_PROFILES_API_TOKEN")
        or PYTEST_DEFAULT_COMMONS_PROFILES_API_TOKEN
    )
    sso_token = (
        os.getenv("COMMONS_SSO_LOGOUT_API_TOKEN")
        or PYTEST_DEFAULT_COMMONS_SSO_LOGOUT_API_TOKEN
    )
    # Keep them distinct even if a caller left SSO unset/equal to Profiles.
    if sso_token == profiles_token:
        sso_token = PYTEST_DEFAULT_COMMONS_SSO_LOGOUT_API_TOKEN
        if sso_token == profiles_token:
            sso_token = f"{profiles_token}-sso"

    monkeypatch.setenv("COMMONS_PROFILES_API_TOKEN", profiles_token)
    monkeypatch.setenv("COMMONS_SSO_LOGOUT_API_TOKEN", sso_token)

    sync_user, _sync_identity = get_durable_service_user("svc-commons-profiles")
    logout_user, _logout_identity = get_durable_service_user("svc-commons-sso")

    app.config["STATIC_API_TOKEN_ROUTES"] = dict(_SPLIT_STATIC_API_TOKEN_ROUTES)
    app.config["STATIC_API_TOKEN_USER_ID_PROFILES"] = sync_user.id
    app.config["STATIC_API_TOKEN_USER_ID_SSO"] = logout_user.id
    register_idms_static_api_token_before_request(app)

    return {"profiles_token": profiles_token, "sso_token": sso_token}


@pytest.fixture(scope="function")
def idms_static_api_auth(idms_static_api_principals) -> dict[str, str]:
    """`Authorization` headers for Profiles sync static-token routes."""
    return {
        "Authorization": f"Bearer {idms_static_api_principals['profiles_token']}",
    }


@pytest.fixture(scope="function")
def idms_sso_static_api_auth(idms_static_api_principals) -> dict[str, str]:
    """`Authorization` headers for SSO logout static-token routes."""
    return {
        "Authorization": f"Bearer {idms_static_api_principals['sso_token']}",
    }


IDMS_MEMBERS_RESPONSE = {
    "username": "gihctester",
    "email": "gihctester@gmail.com",
    "emails": [],
    "name": "Ghost Hc",
    "first_name": "Ghost",
    "last_name": "Hc",
    "institutional_affiliation": None,
    "orcid": "0000-0002-1825-0097",
    "avatar": "https://www.gravatar.com/avatar/e8e059e46712e40575b50a784af4b1deb6a2ce13e113fc246b1a6af129107719?s=150",
    "academic_interests": [],
    "groups": [
        {
            "id": 1004093,
            "group_name": "Educational and Cultural Institutions",
            "role": "member",
            "url": "http://profile.hcommons.org/api/v1/groups/1004093/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1005320,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1005320/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004939,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004939/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004940,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004940/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004941,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004941/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004942,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004942/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004943,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004943/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004944,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004944/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004945,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004945/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004946,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004946/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004947,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004947/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004948,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004948/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004949,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004949/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004950,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004950/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004951,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004951/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004952,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004952/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004953,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004953/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1005109,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1005109/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1005319,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1005319/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1005318,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1005318/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004651,
            "group_name": "Hidden Testing Group New Name",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004651/",
            "status": "public",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004090,
            "group_name": "Humanities, Arts, and Media",
            "role": "member",
            "url": "http://profile.hcommons.org/api/v1/groups/1004090/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004094,
            "group_name": "Publishing and Archives",
            "role": "member",
            "url": "http://profile.hcommons.org/api/v1/groups/1004094/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004092,
            "group_name": "Social and Political Issues",
            "role": "member",
            "url": "http://profile.hcommons.org/api/v1/groups/1004092/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004089,
            "group_name": "Teaching and Learning",
            "role": "member",
            "url": "http://profile.hcommons.org/api/v1/groups/1004089/",
            "status": "public",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
        {
            "id": 1004091,
            "group_name": "Technology, Networks, and Sciences",
            "role": "member",
            "url": "http://profile.hcommons.org/api/v1/groups/1004091/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": None,
        },
    ],
    "memberships": {"MLA": False, "MSU": False, "ARLISNA": False, "UP": False},
    "is_superadmin": False,
}

IDMS_SUBS_RESPONSE_USERNAME = {
    "data": [
        {
            "sub": "http://cilogon.org/serverE/users/XXXXXX",
            "profile": IDMS_MEMBERS_RESPONSE,
            "idp_name": "Gmail",
        }
    ],
    "meta": {"authorized": True},
    "next": None,
    "previous": None,
}

IDMS_SUBS_RESPONSE_SUB = {
    "data": [
        {
            "sub": "http://cilogon.org/serverE/users/XXXXXX",
            "profile": IDMS_MEMBERS_RESPONSE,
            "idp_name": "Gmail",
        }
    ],
    "meta": {"authorized": True},
    "next": None,
    "previous": None,
}
