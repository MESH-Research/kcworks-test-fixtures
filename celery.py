# Part of kcworks-test-fixtures
# Copyright (C) 2026, MESH Research
#
# kcworks-test-fixtures is free software; you can redistribute and/or
# modify it under the terms of the MIT License; see LICENSE file for more details.

"""Celery fixtures for tests.

`celery_config` configures the Celery TestApp used by pytest's `celery_worker`
fixture. That fixture constructs the Celery app, makes it current/default, and
starts a worker thread — that is the Celery app those tests actually use.

`enable_celery_eager` can still toggle eager on the live Celery app for a
single test when needed.
"""

from collections.abc import Generator
from typing import Any

import pytest
from flask import Flask

from tests.fixtures.logging import log_folder_path

test_config_celery: dict[str, Any] = {
    "CELERY_TASK_ALWAYS_EAGER": False,
    "CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS": True,
}

@pytest.fixture(scope="session")
def celery_config(celery_config: dict[str, Any]) -> dict[str, Any]:
    """Configure the Celery TestApp used by `celery_worker`.

    These settings seem to be merged with the Celery settings set via Flask-CeleryExt.
    These settings *override* the initial Flask-CeleryExt settings. In practice this 
    means this config makes the celery_worker fixture's Celery app *eager* (i.e., 
    synchronous).

    Returns:
        dict[str, Any]: Celery configuration for the test Celery app.
    """
    celery_config["logfile"] = str(log_folder_path / "celery.log")
    celery_config["loglevel"] = "DEBUG"
    celery_config["task_always_eager"] = True
    celery_config["cache_backend"] = "memory"
    celery_config["result_backend"] = "cache"
    celery_config["task_eager_propagates_exceptions"] = True
    return celery_config


def _set_celery_eager(flask_app: Flask, *, eager: bool) -> None:
    """Set eager mode on Flask config and the live Celery app.conf."""
    flask_app.config["CELERY_TASK_ALWAYS_EAGER"] = eager
    flask_app.config["CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS"] = True
    celery = flask_app.extensions["flask-celeryext"].celery
    celery.conf.task_always_eager = eager
    celery.conf.task_eager_propagates = True


@pytest.fixture
def enable_celery_eager(running_app) -> Generator[None, None, None]:
    """Run one test with Celery tasks in-process (eager).

    Restores the previous Flask and Celery eager flags after the test.

    Yields:
        None.
    """
    flask_app = running_app.app
    celery = flask_app.extensions["flask-celeryext"].celery
    prev_flask = flask_app.config["CELERY_TASK_ALWAYS_EAGER"]
    prev_celery = celery.conf.task_always_eager
    _set_celery_eager(flask_app, eager=True)
    try:
        yield
    finally:
        flask_app.config["CELERY_TASK_ALWAYS_EAGER"] = prev_flask
        celery.conf.task_always_eager = prev_celery
