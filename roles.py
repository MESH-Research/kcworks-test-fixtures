# Part of KCWorks Test Fixtures
#
# Copyright (C) 2025-2026 MESH Research.
#
# KCWorks Test Fixtures is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Roles related pytest fixtures for testing."""

from collections.abc import Callable, Iterable
from typing import Any

import pytest
from flask_principal import Identity
from invenio_access.models import ActionRoles
from invenio_access.permissions import superuser_access
from invenio_access.utils import get_identity
from invenio_accounts.proxies import current_accounts
from invenio_administration.permissions import administration_access_action
from invenio_db import db


from invenio_group_collections_kcworks.roles import (
    ensure_service_capabilities as ensure_group_collections_capabilities,
)
from invenio_remote_user_data_kcworks.roles import (
    ensure_service_capabilities as ensure_remote_user_data_capabilities,
)


def _allow_action_role(action, role):
    """Grant an access action to a role if not already granted.

    Args:
        action: Access action to grant.
        role: Role that should receive the action.

    Returns:
        The existing or newly created `ActionRoles` row. The caller is
        responsible for committing the session.
    """
    for action_role in ActionRoles.query_by_action(action).all():
        if action_role.role_id == role.id:
            return action_role

    action_role = ActionRoles.create(action=action, role=role)
    db.session.add(action_role)
    return action_role


def _account_user(user: Any) -> Any:
    """Return the Invenio `User` for a fixture wrapper or raw user."""
    return getattr(user, "user", user)


@pytest.fixture(scope="function")
def assign_roles(app, db) -> Callable[..., tuple[Any, Identity]]:
    """Factory: assign role names to an existing user and load their identity.

    Args for the returned callable:
        user: An Invenio `User` or a fixture wrapper with a `.user`
            attribute (e.g. `AugmentedUserFixture`).
        role_names: Role names to assign (created if missing).

    Returns:
        A callable `(user, role_names) -> (user, identity)` that returns the
        same `user` object passed in and a Flask-Principal `Identity` loaded
        via `get_identity` (roles expanded for permission checks).
    """

    def _assign(
        user: Any,
        role_names: Iterable[str],
    ) -> tuple[Any, Identity]:
        account_user = _account_user(user)
        datastore = current_accounts.datastore
        existing = {role.name for role in (account_user.roles or [])}
        for role_name in role_names:
            if role_name in existing:
                continue
            role = datastore.find_or_create_role(name=role_name)
            datastore.add_role_to_user(account_user, role)
            existing.add(role_name)
        datastore.commit()

        merged_user = db.session.merge(account_user)
        identity = get_identity(merged_user)
        return user, identity

    return _assign


@pytest.fixture(scope="session")
def admin_roles(bootstrap_app, database):
    """Create baseline admin roles and inter-app capability roles.

    Links the `administration` / `superuser-access` roles to their access
    actions. Permission policies that use the `Administration` generator emit
    an `administration-access` *action* need; that need only expands to a
    concrete `Need(role="administration")` if the DB has this action->role
    mapping (mirroring production, where the role is granted the action at
    instance setup).

    Inter-app capability roles and service accounts are owned by the 
    remote-user-data and group-collections packages. Those packages also 
    ensure on app finalize, but finalize runs during `bootstrap_app` *before* 
    session `create_all`, so this fixture re-runs the package ensures once 
    tables exist.
    """
    with bootstrap_app.app_context():
        datastore = current_accounts.datastore
        for role_name in (
            "admin-moderator",
            "administration",
            "administration-moderation",
            "superuser-access",
        ):
            if datastore.find_role(role_name) is None:
                datastore.create_role(name=role_name)
        datastore.commit()

        administration_role = datastore.find_role("administration")
        superuser_role = datastore.find_role("superuser-access")
        _allow_action_role(administration_access_action, administration_role)
        _allow_action_role(superuser_access, superuser_role)
        db.session.commit()

        ensure_remote_user_data_capabilities()
        ensure_group_collections_capabilities()
