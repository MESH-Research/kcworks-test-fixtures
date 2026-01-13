# Part of KCWorks Test Fixtures
#
# Copyright (C) 2025 MESH Research.
#
# KCWorks Test Fixtures is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Roles related pytest fixtures for testing."""

import pytest
from invenio_accounts.proxies import current_accounts


@pytest.fixture(scope="module")
def admin_roles():
    """Fixture to create admin roles."""
    current_accounts.datastore.create_role(name="admin-moderator")
    current_accounts.datastore.create_role(name="administration")
    current_accounts.datastore.create_role(name="administration-moderation")
