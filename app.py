# Part of kcworks-test-fixtures
# Copyright (C) 2026, MESH Research
#
# kcworks-test-fixtures is free software; you can redistribute and/or
# modify it under the terms of the MIT License; see LICENSE file for more details.

"""Shared Flask app composition for KCWorks package tests.

Package conftests override via the usual pytest-invenio wrap pattern, e.g.:

```python
@pytest.fixture(scope="module")
def app(app, location, bootstrap_vocabularies, admin_roles):
    register_idms_static_api_token_before_request(app)
    yield app
```

Also override `template_loader_paths` (or `template_loader` entirely),
`create_app`, and `app_config` as needed. Keep package-specific behaviour in
the local conftest — do not add shared hook fixtures for it.
"""

from __future__ import annotations

from collections import namedtuple
from collections.abc import Callable, Generator
from pathlib import Path

import jinja2
import pytest
from flask import Flask
from invenio_queues import current_queues

RunningApp = namedtuple(
    "RunningApp",
    [
        "app",
        "location",
        "cache",
        "create_communities_custom_fields",
        "create_records_custom_fields",
    ],
)


@pytest.fixture(scope="session")
def template_loader_paths() -> list[str | Path]:
    """Override in package conftest with ordered template directories.

    Returns:
        list[str | Path]: Ordered template directories (empty by default).
    """
    return []


@pytest.fixture(scope="session")
def template_loader(
    template_loader_paths: list[str | Path],
) -> Callable[[Flask], None]:
    """Install package template directories on the Flask app Jinja environment.

    Returns:
        Callable[[Flask], None]: Function that attaches loaders to an app.
    """

    def load_templates(app: Flask) -> None:
        existing = [str(path) for path in template_loader_paths if Path(path).exists()]
        if not existing:
            return
        prev_loader = app.jinja_env.loader
        app.jinja_env.loader = jinja2.ChoiceLoader(
            [prev_loader, jinja2.FileSystemLoader(existing)]
        )

    return load_templates


@pytest.fixture(scope="module")
def app(
    app: Flask,
    template_loader: Callable[[Flask], None],
) -> Generator[Flask, None, None]:
    """Compose the pytest-invenio app with shared queue declare and templates.

    Yields:
        The Flask application instance.
    """
    with app.app_context():
        current_queues.declare()
    template_loader(app)
    yield app


@pytest.fixture(scope="function")
def running_app(
    app: Flask,
    location,
    cache,
    create_communities_custom_fields,
    create_records_custom_fields,
) -> RunningApp:
    """Bundle the fixtures most service tests need together.

    Returns:
        RunningApp: Named tuple of app plus common data fixtures.
    """
    return RunningApp(
        app,
        location,
        cache,
        create_communities_custom_fields,
        create_records_custom_fields,
    )
