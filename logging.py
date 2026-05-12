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
"""

import logging
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def quiet_third_party_loggers() -> None:
    """Raise noisy third-party loggers above the default test verbosity."""
    logging.getLogger("celery").setLevel(logging.WARNING)
    logging.getLogger("opensearch").setLevel(logging.WARNING)
    logging.getLogger("opensearchpy").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.INFO)


@pytest.fixture(scope="session")
def celery_enable_logging() -> bool:
    """Enable Celery logging for tests.

    Returns:
        bool: True to enable Celery logging.
    """
    return False


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
