# Part of KCWorks Test Fixtures
# Copyright (C) 2026, MESH Research.
#
# KCWorks Test Fixtures is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Fixtures and helpers for association webhook and task tests."""

from typing import Any

ASSOCIATION_OAUTH_ID = "http://cilogon.org/serverE/users/523864"


def association_webhook_payload(
    kc_id: str,
    oauth_id: str = ASSOCIATION_OAUTH_ID,
    *,
    nested: bool = False,
) -> dict[str, Any]:
    """Build an association webhook POST body.

    Args:
        kc_id: KC username for the association event.
        oauth_id: CILogon subject identifier.
        nested: When True, use the sender's top-level ``associations`` wrapper.

    Returns:
        Webhook JSON body suitable for ``/api/webhooks/users/update``.
    """
    event = {"id": oauth_id, "kc_id": kc_id, "event": "associated"}
    if nested:
        return {"idp": "cilogon", "associations": {"associations": [event]}}
    return {"idp": "cilogon", "updates": {"associations": [event]}}
