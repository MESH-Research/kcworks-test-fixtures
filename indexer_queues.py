# Part of Knowledge Commons Works
# Copyright (C) 2026 MESH Research
#
# KCWorks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Fixtures for keeping indexer message queues clean between tests.

Indexer bulk ops publish to RabbitMQ. The function-scoped ``db`` fixture rolls
back SQLAlchemy state, but MQ messages survive. Later ``process_bulk_queue()``
calls then try to index missing users (``UserAggregate.get_record`` returns
``None``) and log ``AttributeError: 'NoneType' object has no attribute
'index'``.
"""

from __future__ import annotations

import logging

import pytest
from kombu.exceptions import OperationalError

logger = logging.getLogger(__name__)


def purge_indexer_mq_queues() -> None:
    """Purge all registered indexer queues plus the default INDEXER_MQ_QUEUE.

    Must run inside a Flask application context.
    """
    from celery.messaging import establish_connection
    from flask import current_app
    from invenio_indexer.proxies import current_indexer_registry

    queues = [indexer.mq_queue for indexer in current_indexer_registry.all().values()]
    queues.append(current_app.config["INDEXER_MQ_QUEUE"])

    seen_names: set[str] = set()
    try:
        with establish_connection() as conn:
            for queue in queues:
                name = getattr(queue, "name", None) or str(queue)
                if name in seen_names:
                    continue
                seen_names.add(name)
                bound = queue(conn)
                try:
                    bound.purge()
                except Exception:
                    # Queue may not exist yet in a fresh broker.
                    try:
                        bound.declare()
                        bound.purge()
                    except Exception:
                        logger.debug(
                            "Could not purge indexer queue %s", name, exc_info=True
                        )
    except OperationalError:
        logger.debug("Indexer queue purge skipped; broker unavailable", exc_info=True)


@pytest.fixture(scope="function", autouse=True)
def purge_indexer_mq_between_tests(request: pytest.FixtureRequest):
    """Purge indexer MQ before/after tests that use the Flask app.

    Avoids pulling ``app`` into tests that never request it.
    """
    uses_app = "app" in request.fixturenames or "running_app" in request.fixturenames
    if not uses_app:
        yield
        return

    app = request.getfixturevalue("app")
    with app.app_context():
        purge_indexer_mq_queues()
    yield
    with app.app_context():
        purge_indexer_mq_queues()
