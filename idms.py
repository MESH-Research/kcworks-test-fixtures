# Part of KCWorks Test Fixtures
# Copyright (C) 2026, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test fixtures related to remote IDMS actions."""

import os
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


def _route_token_env_for_request(path: str, routes_map: dict[str, str]) -> str | None:
    """Return the token env var name for `path`, or `None`."""
    if not routes_map:
        return None
    matches = [
        (prefix, env_var)
        for prefix, env_var in routes_map.items()
        if path.startswith(prefix)
    ]
    if not matches:
        return None
    most_specific = max(matches, key=lambda p: len([s for s in p[0].split("/") if s]))
    return most_specific[1]


def _idms_static_api_token_before_request() -> None:
    """If path + Bearer match `STATIC_API_TOKEN_ROUTES`, impersonate configured user.

    Mirrors KCWorks `site/kcworks/ext.py`; installed from `tests.conftest` for API
    tests that use `create_api` without the site `api_finalize_app` hook.
    """
    if getattr(request, "oauth_verify_has_run", False):
        return

    routes_map = current_app.config.get("STATIC_API_TOKEN_ROUTES") or {}
    token_env_var = _route_token_env_for_request(request.path, routes_map)
    if not token_env_var:
        return
    static_token = os.environ.get(token_env_var)
    if not static_token:
        return
    try:
        token = extract_bearer_token(request.headers.get("Authorization") or "")
    except ValueError:
        return
    if token != static_token:
        return

    user_id = current_app.config.get("STATIC_API_TOKEN_USER_ID")
    if user_id is None:
        return
    user = current_datastore.find_user(id=user_id)
    if not user or not user.active:
        return

    g._login_user = user
    identity_changed.send(
        current_app._get_current_object(),
        identity=Identity(user.id),  # type: ignore[arg-type]
    )
    scopes = {sid for sid, _ in current_oauth2server.scope_choices()}
    request.oauth = _OAuthStandIn(  # type: ignore[attr-defined]
        user=user,
        access_token=_AccessTokenStandIn(scopes=scopes),
    )
    request.skip_csrf_check = True  # type: ignore[attr-defined]
    request.oauth_verify_has_run = True  # type: ignore[attr-defined]


def register_idms_static_api_token_before_request(app) -> None:
    """Prepend the IDMS static-token handler when `STATIC_API_TOKEN_*` is set."""
    routes_map = app.config.get("STATIC_API_TOKEN_ROUTES") or {}
    static_user_id = app.config.get("STATIC_API_TOKEN_USER_ID")
    if not routes_map or static_user_id is None:
        return
    funcs = app.before_request_funcs.get(None, [])
    if _idms_static_api_token_before_request in funcs:
        return
    app.before_request_funcs[None] = [_idms_static_api_token_before_request] + funcs


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


_IDMS_STATIC_API_TEST_TOKEN = "test-idms-static-api-token"


@pytest.fixture(scope="function")
def idms_static_api_auth(
    app,
    admin,
    admin_role_need,
    monkeypatch,
) -> dict[str, str]:
    """HTTP headers with `Authorization: Bearer` for IDMS static-token routes.

    Sets `TEST_IDMS_STATIC_API_TOKEN` (see `STATIC_API_TOKEN_ROUTES` in test
    config) and `STATIC_API_TOKEN_USER_ID` to `admin` so the before-request
    hook matches production KCWorks behaviour.

    Args:
        app: Flask application.
        admin: User whose id is configured as the static-token principal.
        admin_role_need: Links `administration_access_action` to the admin role.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        Headers dict suitable for requests to routes listed in
        `STATIC_API_TOKEN_ROUTES`.
    """
    monkeypatch.setenv("TEST_IDMS_STATIC_API_TOKEN", _IDMS_STATIC_API_TEST_TOKEN)
    app.config["STATIC_API_TOKEN_USER_ID"] = admin.user.id
    return {"Authorization": f"Bearer {_IDMS_STATIC_API_TEST_TOKEN}"}


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
