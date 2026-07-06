# Part of invenio-remote-user-data-kcworks
# Copyright (C) 2023-2026, MESH Research
#
# invenio-remote-user-data-kcworks is free software; you can redistribute and/or
# modify it under the terms of the MIT License; see LICENSE file for more details.

"""Search index fixtures for tests."""

from collections.abc import Generator

import pytest
from invenio_search.proxies import current_search_client
from opensearchpy import OpenSearch

PRESERVED_SEARCH_ALIASES = {
    "vocabularies",
    "awards",
    "affiliations",
    "subjects",
    "funders",
}


def _leaf_alias_names(tree: dict) -> list[str]:
    """Return logical leaf alias names from an Invenio alias tree."""
    names: list[str] = []
    for name, value in tree.items():
        if isinstance(value, dict):
            names.extend(_leaf_alias_names(value))
        else:
            names.append(name)
    return names


@pytest.fixture(scope="function")
def search_clear(search) -> Generator[OpenSearch, None, None]:
    """Reset mutable search indices, but preserve seeded vocabulary aliases.

    Yields:
        The active OpenSearch client fixture.
    """
    from invenio_communities.proxies import current_identities_cache
    from invenio_search import current_search

    from tests.fixtures.vocabularies.rebuild_helpers import clear_vocabulary_label_caches
    from tests.fixtures.vocabularies.resource_types import TYPE_ID

    clear_vocabulary_label_caches(TYPE_ID)
    current_identities_cache.flush()

    registered_aliases = set(_leaf_alias_names(current_search.active_aliases))
    reset_aliases = sorted(registered_aliases - PRESERVED_SEARCH_ALIASES)

    yield search

    if reset_aliases:
        list(current_search.delete(ignore=[404], index_list=reset_aliases))
        list(current_search.create(index_list=reset_aliases))

    current_search_client.indices.delete("*stats*", ignore=[404])
    current_search_client.indices.delete_template("*stats*", ignore=[404])
    current_search_client.indices.refresh(index="*")
