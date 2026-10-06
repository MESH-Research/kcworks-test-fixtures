# Part of KCWorks Test Fixtures
#
# Copyright (C) 2025 MESH Research.
#
# KCWorks Test Fixtures is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Roles related pytest fixtures for testing."""

import pytest
from invenio_access.models import ActionRoles
from invenio_access.permissions import superuser_access
from invenio_accounts.proxies import current_accounts
from invenio_administration.permissions import administration_access_action
from invenio_db import db


def _allow_action_role(action, role):
    """Grant an access action to a role if not already granted.

    Args:
        action: Access action to grant.
        role: Role that should receive the action.

    Returns:
        The existing or newly created ``ActionRoles`` row. The caller is
        responsible for committing the session.
    """
    for action_role in ActionRoles.query_by_action(action).all():
        if action_role.role_id == role.id:
            return action_role

    action_role = ActionRoles.create(action=action, role=role)
    db.session.add(action_role)
    return action_role


@pytest.fixture(scope="session")
def admin_roles(bootstrap_app, database):
    """Create baseline admin roles and their access-action mappings.

    Besides creating the role rows, this links the ``administration`` role to
    the ``administration-access`` action. Permission policies that use the
    ``Administration`` generator emit an ``administration-access`` *action*
    need; that need only expands to a concrete ``Need(role="administration")``
    if the DB has this action->role mapping (mirroring production, where the
    role is granted the action at instance setup).

    Also ensures the four inter-app service capability roles
    (``users-sync``, ``groups-sync``, ``users-logout``,
    ``group-collections-write``) exist with their ActionRoles bindings.
    """
    from invenio_group_collections_kcworks.permissions import (
        group_collections_write_action,
    )
    from invenio_remote_user_data_kcworks.permissions import (
        groups_sync_action,
        users_logout_action,
        users_sync_action,
    )

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
