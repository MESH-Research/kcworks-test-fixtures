# Part of invenio-remote-user-data-kcworks
# Copyright (C) 2023-2026, MESH Research
#
# invenio-remote-user-data-kcworks is free software; you can redistribute and/or
# modify it under the terms of the MIT License; see LICENSE file for more details.

"""Logging fixtures for tests.

Note:
    Celery not only configures its own parent logger will child loggers per-module,
    it also reconfigures the root Python logger. In particular it sets the root logger
    level (by default to "ERROR"). So if we want to see other loggers' output at lower
    levels we have to give celery a different basic loglevel and then manually
    configure the individual loggers that we want to be quieter.

    Separately, each module-scoped Flask app init installs new console/FS handlers on
    the shared `app.logger` name via `InvenioLoggingConsole` /
    `InvenioLoggingFS`. Those handlers are never removed, so full-suite runs
    multiply every log line. `dedupe_app_logger_handlers` keeps one handler per
    class.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest
from flask import Flask


def dedupe_app_logger_handlers(app: Flask) -> None:
    """Keep a single handler per class on `app.logger`.

    `InvenioLoggingConsole.install_handler` and `InvenioLoggingFS.install_handler`
    always `addHandler` on the named Flask logger. Module-scoped app recreation
    therefore stacks `StreamHandler` / `RotatingFileHandler` instances across the
    suite. Prefer the most recently added handler of each class.

    Plain `StreamHandler` instances are collapsed together (including across
    trivial subclasses) so console output is not multiplied; other handler types
    are keyed by their concrete class.
    """
    logger = app.logger
    keep_by_class: dict[type[logging.Handler], logging.Handler] = {}
    for handler in list(logger.handlers):
        key: type[logging.Handler]
        if isinstance(handler, RotatingFileHandler):
            key = RotatingFileHandler
        elif isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, logging.FileHandler
        ):
            # FileHandler is a StreamHandler subclass; don't fold it in.
            key = logging.StreamHandler
        else:
            key = type(handler)
        previous = keep_by_class.get(key)
        if previous is not None and previous is not handler:
            logger.removeHandler(previous)
        keep_by_class[key] = handler


@pytest.fixture(scope="module", autouse=True)
def dedupe_app_logger_handlers_on_app(request: pytest.FixtureRequest):
    """Dedupe Flask app logger handlers once per test module that uses an app.

    Registering `tests.fixtures.logging` as a pytest plugin is enough; packages
    do not need to call this from their own `app` fixture.
    """
    uses_app = any(
        name in request.fixturenames for name in ("app", "base_app", "running_app")
    )
    if not uses_app:
        yield
        return

    app_fixture = "app" if "app" in request.fixturenames else "base_app"
    app = request.getfixturevalue(app_fixture)
    dedupe_app_logger_handlers(app)
    yield


@pytest.fixture(scope="session", autouse=True)
def quiet_third_party_loggers() -> None:
    """Raise noisy third-party loggers above the default test verbosity."""
    logging.getLogger("celery").setLevel(logging.WARNING)
    logging.getLogger("opensearch").setLevel(logging.WARNING)
    logging.getLogger("opensearchpy").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.INFO)
    # PersistentIdentifier.create logs INFO per row; session vocab bootstrap
    # creates hundreds. Keep WARNING+ (e.g. IntegrityError exceptions).
    logging.getLogger("invenio-pidstore").setLevel(logging.WARNING)


@pytest.fixture(scope="session")
def celery_enable_logging() -> bool:
    """Enable Celery logging on pytest's Celery TestApp.

    Passed to `celery.contrib.pytest` when it builds the session/function
    Celery app used by `celery_worker`. When True, that TestApp runs
    Celery's normal logging setup instead of leaving loggers quiet.

    Returns:
        bool: True to enable Celery logging.
    """
    return True


@pytest.fixture(scope="session")
def celery_worker_parameters() -> dict:
    """Add config to individual celery workers.

    Returns:
        The per-worker logging configuration.
    """
    return {"loglevel": "DEBUG"}


# --- Logging config settings -----------------------------------------------
parent_path = Path(__file__).parent
log_folder_path = parent_path / "test_logs"
log_file_path = log_folder_path / "invenio.log"
if not log_file_path.exists():
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    log_file_path.touch()

test_config_logging = {}
test_config_logging["LOGGING_FS_LEVEL"] = "DEBUG"
test_config_logging["LOGGING_FS_LOGFILE"] = str(log_file_path)
test_config_logging["LOGGING_CONSOLE"] = True
test_config_logging["LOGGING_CONSOLE_LEVEL"] = "DEBUG"
test_config_logging["CELERY_LOGFILE"] = str(log_folder_path / "celery.log")
