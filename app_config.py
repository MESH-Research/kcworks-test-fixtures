# Part of kcworks-test-fixtures
# Copyright (C) 2026, MESH Research
#
# kcworks-test-fixtures is free software; you can redistribute and/or
# modify it under the terms of the MIT License; see LICENSE file for more details.

"""Shared Flask/Invenio test configuration.

`test_config` is the baseline dict (also used by session bootstrap). Domain
fragments live in sibling modules (`test_config_mail`, `test_config_urls`,
…). Package conftests should wrap `app_config` for suite-specific keys
instead of rebuilding the whole dict:

```python
@pytest.fixture(scope="module")
def app_config(app_config):
    app_config["MY_PACKAGE_SETTING"] = "..."
    return app_config
```
"""

from __future__ import annotations

import ast
import os
from typing import Any

import pytest

from tests.fixtures.celery import test_config_celery
from tests.fixtures.custom_fields import test_config_fields
from tests.fixtures.frontend import test_config_frontend
from tests.fixtures.identifiers import test_config_identifiers
from tests.fixtures.idms import test_config_idms
from tests.fixtures.logging import test_config_logging
from tests.fixtures.mail import test_config_mail
from tests.fixtures.names import test_config_names
from tests.fixtures.stats import test_config_stats
from tests.fixtures.urls import test_config_urls
from tests.fixtures.users import test_config_accounts

test_config: dict[str, Any] = {
    **test_config_identifiers,
    **test_config_fields,
    **test_config_logging,
    **test_config_mail,
    **test_config_celery,
    **test_config_frontend,
    **test_config_urls,
    **test_config_idms,
    **test_config_accounts,
    **test_config_names,
    **test_config_stats,
    "SEARCH_INDEX_PREFIX": "",
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    # Root baseline: non-eager so Celery/indexer MQ behaviour is exercised.
    # Suites that want in-process tasks override in their `app_config` wrap.
    "DEBUG": True,
    "BABEL_DEFAULT_TIMEZONE": "America/Detroit",
}


def apply_connection_env(app_config: dict[str, Any]) -> dict[str, Any]:
    """Overlay docker-services-cli / compose connection env onto app config.

    Args:
        app_config: Mutable Flask/Invenio config mapping.

    Returns:
        The same mapping, updated in place.
    """
    # Test-services URI only (docker-services-cli / test-runner) — not
    # INVENIO_SQLALCHEMY_* (app/runtime DB). Env when set; else the host
    # mapping docker-services-cli exports. Without this, create_app falls
    # through to invenio_app_rdm's invenio-app-rdm@localhost default.
    app_config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql+psycopg2://invenio:invenio@localhost:5432/invenio",
    )
    # Same pattern as DB: docker-services-cli / test-runner env when set,
    # else the host default packages used to hard-code.
    broker_url = os.environ.get(
        "BROKER_URL",
        "amqp://guest:guest@localhost:5672//",
    )
    app_config["BROKER_URL"] = broker_url
    app_config["CELERY_BROKER_URL"] = broker_url
    app_config["QUEUES_BROKER_URL"] = broker_url
    if os.environ.get("CACHE_REDIS_URL"):
        app_config["CACHE_REDIS_URL"] = os.environ["CACHE_REDIS_URL"]
        app_config["CACHE_TYPE"] = "redis"
    if os.environ.get("ACCOUNTS_SESSION_REDIS_URL"):
        app_config["ACCOUNTS_SESSION_REDIS_URL"] = os.environ[
            "ACCOUNTS_SESSION_REDIS_URL"
        ]
    if os.environ.get("CELERY_RESULT_BACKEND"):
        app_config["CELERY_RESULT_BACKEND"] = os.environ["CELERY_RESULT_BACKEND"]
    if os.environ.get("RATELIMIT_STORAGE_URI"):
        app_config["RATELIMIT_STORAGE_URI"] = os.environ["RATELIMIT_STORAGE_URI"]
        app_config["RATELIMIT_STORAGE_URL"] = os.environ["RATELIMIT_STORAGE_URI"]
    if os.environ.get("COMMUNITIES_IDENTITIES_CACHE_REDIS_URL"):
        app_config["COMMUNITIES_IDENTITIES_CACHE_REDIS_URL"] = os.environ[
            "COMMUNITIES_IDENTITIES_CACHE_REDIS_URL"
        ]

    raw_hosts = os.environ.get("SEARCH_HOSTS", "").strip()
    if raw_hosts:
        hosts = ast.literal_eval(raw_hosts)
        app_config["SEARCH_HOSTS"] = hosts
        client_cfg = dict(app_config.get("SEARCH_CLIENT_CONFIG") or {})
        client_cfg["hosts"] = hosts
        app_config["SEARCH_CLIENT_CONFIG"] = client_cfg

    return app_config


@pytest.fixture(scope="module")
def app_config(app_config: dict[str, Any]) -> dict[str, Any]:
    """Merge shared test defaults into pytest-invenio's `app_config`.

    Returns:
        dict[str, Any]: The shared test application config.
    """
    for key, value in test_config.items():
        app_config[key] = value
    return apply_connection_env(app_config)
