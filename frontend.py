# Part of KCWorks Test Fixtures
# Copyright (C) 2024-2025, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Pytest fixtures for frontend."""

from flask_webpackext.manifest import (
    JinjaManifest,
    JinjaManifestEntry,
    JinjaManifestLoader,
)


class MockJinjaManifest(JinjaManifest):
    """Mock the webpack manifest to avoid having to compile the full assets."""

    def __getitem__(self, key):
        """Get a manifest entry.

        Returns:
            JinjaManifestEntry: A manifest entry for the given key.
        """
        return JinjaManifestEntry(key, [key])

    def __getattr__(self, name):
        """Get a manifest entry.

        Returns:
            JinjaManifestEntry: A manifest entry for the given name.
        """
        return JinjaManifestEntry(name, [name])


class MockManifestLoader(JinjaManifestLoader):
    """Manifest loader creating a mocked manifest."""

    def load(self, filepath):
        """Load the manifest.

        Returns:
            MockJinjaManifest: A mocked manifest instance.
        """
        return MockJinjaManifest()
