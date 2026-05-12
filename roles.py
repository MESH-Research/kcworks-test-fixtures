# Part of KCWorks Test Fixtures
#
# Copyright (C) 2025 MESH Research.
#
# KCWorks Test Fixtures is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Roles related pytest fixtures for testing."""

import pytest
from invenio_accounts.proxies import current_accounts


@pytest.fixture(scope="session")
def admin_roles(bootstrap_app, database):
    """Fixture to create admin roles."""
    with bootstrap_app.app_context():
        for role_name in (
            "admin-moderator",
            "administration",
            "administration-moderation",
        ):
            if current_accounts.datastore.find_role(role_name) is None:
                current_accounts.datastore.create_role(name=role_name)
        current_accounts.datastore.commit()
