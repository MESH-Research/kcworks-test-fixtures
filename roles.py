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
from flask_principal import Identity, identity_changed
from invenio_access.models import ActionRoles
from invenio_access.permissions import superuser_access
from invenio_accounts.proxies import current_accounts
from invenio_administration.permissions import administration_access_action
from invenio_db import db


from invenio_group_collections_kcworks.permissions import (
    group_collections_write_action,
)
from invenio_remote_user_data_kcworks.permissions import (
    groups_sync_action,
    users_logout_action,
    users_sync_action,
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
        same `user` object passed in and a Flask-Principal `Identity` with
        roles expanded via `identity_changed`.
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

        identity = Identity(account_user.id)
        identity_changed.send(app, identity=identity)
        return user, identity

    return _assign


@pytest.fixture(scope="session")
def admin_roles(bootstrap_app, database):
    """Create baseline admin roles and their access-action mappings.

    Besides creating the role rows, this links the `administration` role to
    the `administration-access` action. Permission policies that use the
    `Administration` generator emit an `administration-access` *action*
    need; that need only expands to a concrete `Need(role="administration")`
    if the DB has this action->role mapping (mirroring production, where the
    role is granted the action at instance setup).

    Also ensures the four inter-app service capability roles
    (`users-sync`, `groups-sync`, `users-logout`,
    `group-collections-write`) exist with their ActionRoles bindings.
    """
    with bootstrap_app.app_context():
        datastore = current_accounts.datastore
        for role_name in (
            "admin-moderator",
            "administration",
            "administration-moderation",
            "superuser-access",
            "users-sync",
            "groups-sync",
            "users-logout",
            "group-collections-write",
        ):
            if datastore.find_role(role_name) is None:
                datastore.create_role(name=role_name)
        datastore.commit()

        administration_role = datastore.find_role("administration")
        superuser_role = datastore.find_role("superuser-access")
        _allow_action_role(administration_access_action, administration_role)
        _allow_action_role(superuser_access, superuser_role)
        _allow_action_role(users_sync_action, datastore.find_role("users-sync"))
        _allow_action_role(groups_sync_action, datastore.find_role("groups-sync"))
        _allow_action_role(users_logout_action, datastore.find_role("users-logout"))
        _allow_action_role(
            group_collections_write_action,
            datastore.find_role("group-collections-write"),
        )
        db.session.commit()
