# Part of KCWorks Test Fixtures
# Copyright (C) 2026 MESH Research
#
# kcworks-test-fixtures is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest fixtures for dealing with UnitOfWork operations."""

import pytest
from invenio_records_resources.services.uow import UnitOfWork as OriginalUoW
from sqlalchemy.exc import InvalidRequestError, ResourceClosedError


@pytest.fixture
def nested_unit_of_work():
    """Provide a test-friendly UnitOfWork that uses nested transactions.

    Returns:
        NestedUnitOfWork: A class to use in monkeypatching the UnitOfWork
            where rollbacks create problems in nested test transaction
            contexts.
    """

    class NestedUnitOfWork(OriginalUoW):
        """UnitOfWork that uses nested transactions for test isolation."""

        def __init__(self, session=None):
            super().__init__(session)
            self._nested = None

        def __enter__(self):
            # Only create nested transaction if we don't already have one
            if self._nested is None:
                try:
                    self._nested = self._session.begin_nested()
                except (ResourceClosedError, InvalidRequestError):
                    # Session already has an active nested transaction
                    pass
            return super().__enter__()

        def rollback(self):
            """Rollback only to this UnitOfWork's SAVEPOINT."""
            # Try to rollback nested transaction if it exists and is active
            if self._nested:
                try:
                    self._nested.rollback()
                except (ResourceClosedError, InvalidRequestError):
                    # Transaction already closed/rolled back - that's ok
                    pass

            # Run operation callbacks (original behavior)
            for op in self._operations:
                op.on_rollback(self)
            for op in self._operations:
                op.on_post_rollback(self)

        def commit(self):
            """Commit the nested transaction, then the outer session."""
            # Try to commit nested transaction if it exists and is active
            if self._nested:
                try:
                    self._nested.commit()
                except (ResourceClosedError, InvalidRequestError):
                    # Transaction already closed/committed - that's ok
                    pass

            # Then commit the session (original behavior)
            self.session.commit()

            # Run commit operations (original behavior)
            for op in self._operations:
                op.on_commit(self)
            for op in self._operations:
                op.on_post_commit(self)

            self._mark_dirty()

    return NestedUnitOfWork
