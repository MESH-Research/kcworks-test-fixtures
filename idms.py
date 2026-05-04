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


IDMS_MEMBERS_RESPONSE = {
    "username": "gihctester",
    "email": "gihctester@gmail.com",
    "emails": [],
    "name": "Ghost Hc",
    "first_name": "Ghost",
    "last_name": "Hc",
    "institutional_affiliation": null,
    "orcid": "",
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
            "inviter": null,
        },
        {
            "id": 1005320,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1005320/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004939,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004939/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004940,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004940/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004941,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004941/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004942,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004942/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004943,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004943/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004944,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004944/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004945,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004945/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004946,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004946/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004947,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004947/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004948,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004948/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004949,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004949/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004950,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004950/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004951,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004951/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004952,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004952/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004953,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004953/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1005109,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1005109/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1005319,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1005319/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1005318,
            "group_name": "GI Hidden Group for testing",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1005318/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004651,
            "group_name": "Hidden Testing Group New Name",
            "role": "administrator",
            "url": "http://profile.hcommons.org/api/v1/groups/1004651/",
            "status": "public",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004090,
            "group_name": "Humanities, Arts, and Media",
            "role": "member",
            "url": "http://profile.hcommons.org/api/v1/groups/1004090/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004094,
            "group_name": "Publishing and Archives",
            "role": "member",
            "url": "http://profile.hcommons.org/api/v1/groups/1004094/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004092,
            "group_name": "Social and Political Issues",
            "role": "member",
            "url": "http://profile.hcommons.org/api/v1/groups/1004092/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004089,
            "group_name": "Teaching and Learning",
            "role": "member",
            "url": "http://profile.hcommons.org/api/v1/groups/1004089/",
            "status": "public",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
        {
            "id": 1004091,
            "group_name": "Technology, Networks, and Sciences",
            "role": "member",
            "url": "http://profile.hcommons.org/api/v1/groups/1004091/",
            "status": "hidden",
            "avatar": "",
            "inviter_id": 0,
            "inviter": null,
        },
    ],
    "memberships": {"MLA": false, "MSU": false, "ARLISNA": false, "UP": false},
    "is_superadmin": false,
}

IDMS_SUBS_RESPONSE_USERNAME = {
    "data": [
        {
            "sub": "http://cilogon.org/serverE/users/XXXXXX",
            "profile": IDMS_MEMBERS_RESPONSE,
            "idp_name": "Gmail",
        }
    ],
    "meta": {"authorized": true},
    "next": null,
    "previous": null,
}

IDMS_SUBS_RESPONSE_SUB = {
    "data": [
        {
            "sub": "http://cilogon.org/serverE/users/XXXXXX",
            "profile": IDMS_MEMBERS_RESPONSE,
            "idp_name": "Gmail",
        }
    ],
    "meta": {"authorized": true},
    "next": null,
    "previous": null,
}
