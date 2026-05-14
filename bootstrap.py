# Part of kcworks-test-fixtures
# Copyright (C) 2023-2026, MESH Research
#
# kcworks-test-fixtures is free software; you can redistribute and/or
# modify it under the terms of the MIT License; see LICENSE file for more details.

"""Fixtures to bootstrap heavy vocabularies in the db and search.

These fixtures do two things:
    1. They replace the module-scoped database and search fixtures with
       session scoped versions so that they do not tear down the heavy
       fixture data between modules.
    2. They provide a session-scoped loader for heavy vocabulary fixtures.

This must be paired with a search_clear fixture that does not delete the vocabulary
indices each time.

Use by importing the module into conftest.py and adding `bootstrap_vocabularies` to
the `app` fixture arguments.
"""

import os
import shutil
import sys
import tempfile
from collections.abc import Generator

import pytest
from flask import Flask
from invenio_app.factory import create_api as create_bootstrap_app
from invenio_db import db as db_
from invenio_files_rest.models import Location
from invenio_queues import current_queues
from invenio_search.engine import search as search_engine
from invenio_search.proxies import current_search, current_search_client
from invenio_vocabularies.contrib.affiliations.api import Affiliation
from invenio_vocabularies.contrib.awards.api import Award
from invenio_vocabularies.contrib.funders.api import Funder
from invenio_vocabularies.contrib.subjects.api import Subject
from invenio_vocabularies.records.api import Vocabulary
from sqlalchemy_utils.functions import create_database, database_exists

from tests.conftest import test_config
from tests.fixtures.idms import register_idms_static_api_token_before_request
from tests.fixtures.vocabularies.affiliations import ensure_affiliations_vocabulary
from tests.fixtures.vocabularies.community_types import (
    ensure_community_types_vocabulary,
)
from tests.fixtures.vocabularies.date_types import ensure_date_types_vocabulary
from tests.fixtures.vocabularies.descriptions import (
    ensure_description_types_vocabulary,
)
from tests.fixtures.vocabularies.funding_and_awards import (
    ensure_awards_vocabulary,
    ensure_funders_vocabulary,
)
from tests.fixtures.vocabularies.languages import ensure_languages_vocabulary
from tests.fixtures.vocabularies.licenses import ensure_licenses_vocabulary
from tests.fixtures.vocabularies.resource_types import ensure_resource_types_vocabulary
from tests.fixtures.vocabularies.roles import (
    ensure_contributors_roles_vocabulary,
    ensure_creators_roles_vocabulary,
)
from tests.fixtures.vocabularies.subjects import ensure_subjects_vocabulary
from tests.fixtures.vocabularies.title_types import ensure_title_types_vocabulary

PRESERVED_SEARCH_ALIASES = {
    "vocabularies",
    "awards",
    "affiliations",
    "subjects",
    "funders",
}


def _leaf_alias_names(tree: dict) -> list[str]:
    names: list[str] = []
    for name, value in tree.items():
        if isinstance(value, dict):
            names.extend(_leaf_alias_names(value))
        else:
            names.append(name)
    return names


@pytest.fixture(scope="session")
def bootstrap_instance_path() -> Generator[str, None, None]:
    """Provide an isolated instance path for session-scoped bootstrap.

    Yields:
        The temporary instance path used by the bootstrap app.
    """
    path = tempfile.mkdtemp(prefix="irud-bootstrap-")
    old_instance = os.environ.get("INVENIO_INSTANCE_PATH")
    old_static = os.environ.get("INVENIO_STATIC_FOLDER")

    os.environ["INVENIO_INSTANCE_PATH"] = path
    os.environ["INVENIO_STATIC_FOLDER"] = os.path.join(
        sys.prefix, "var/instance/static"
    )

    try:
        yield path
    finally:
        if old_instance is None:
            os.environ.pop("INVENIO_INSTANCE_PATH", None)
        else:
            os.environ["INVENIO_INSTANCE_PATH"] = old_instance

        if old_static is None:
            os.environ.pop("INVENIO_STATIC_FOLDER", None)
        else:
            os.environ["INVENIO_STATIC_FOLDER"] = old_static

        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(scope="session")
def bootstrap_app(bootstrap_instance_path: str) -> Flask:
    """Create the session app used only for DB/search/vocabulary bootstrap.

    Returns:
        The bootstrap Flask application.
    """
    app = create_bootstrap_app(**dict(test_config))
    with app.app_context():
        current_queues.declare()
    register_idms_static_api_token_before_request(app)
    return app


@pytest.fixture(scope="session")
def database(bootstrap_app: Flask) -> Generator[object, None, None]:
    """Create the session-scoped test database.

    Yields:
        The configured database handle.
    """
    with bootstrap_app.app_context():
        db_url = str(db_.engine.url.render_as_string(hide_password=False))
        if not database_exists(db_url):
            create_database(db_url)
        db_.create_all()

    yield db_

    with bootstrap_app.app_context():
        db_.session.remove()
        db_.drop_all()


@pytest.fixture(scope="session")
def location(
    bootstrap_app: Flask,
    database: object,
) -> Generator[Location, None, None]:
    """Create the default files `Location` used by tests.

    Yields:
        The created default `Location`.
    """
    uri = tempfile.mkdtemp()
    location_obj = Location(name="pytest-location", uri=uri, default=True)

    with bootstrap_app.app_context():
        db_.session.add(location_obj)
        db_.session.commit()

    yield location_obj

    shutil.rmtree(uri, ignore_errors=True)


@pytest.fixture(scope="session")
def search(bootstrap_app: Flask) -> Generator[object, None, None]:
    """Create the session-scoped search indices.

    Yields:
        The active search client.
    """
    with bootstrap_app.app_context():
        try:
            list(current_search.create())
        except search_engine.RequestError:
            list(current_search.delete(ignore=[404]))
            list(current_search.create())
        current_search_client.indices.refresh(index="*")

    yield current_search_client

    with bootstrap_app.app_context():
        list(current_search.delete(ignore=[404]))


@pytest.fixture(scope="session")
def bootstrap_vocabularies(
    bootstrap_app: Flask,
    database: object,
    search: object,
) -> None:
    """Seed heavy vocabularies once into DB and search."""
    with bootstrap_app.app_context():
        ensure_affiliations_vocabulary(refresh=False)
        ensure_community_types_vocabulary(refresh=False)
        ensure_date_types_vocabulary(refresh=False)
        ensure_description_types_vocabulary(refresh=False)
        ensure_languages_vocabulary(refresh=False)
        ensure_licenses_vocabulary(refresh=False)
        ensure_resource_types_vocabulary(refresh=False)
        ensure_creators_roles_vocabulary(refresh=False)
        ensure_contributors_roles_vocabulary(refresh=False)
        ensure_title_types_vocabulary(refresh=False)
        ensure_funders_vocabulary(refresh=False)
        ensure_awards_vocabulary(refresh=False)
        ensure_subjects_vocabulary(refresh=False)

        Vocabulary.index.refresh()
        Affiliation.index.refresh()
        Subject.index.refresh()
        if Funder:
            Funder.index.refresh()
        if Award:
            Award.index.refresh()

        current_search_client.indices.refresh(index="*")
