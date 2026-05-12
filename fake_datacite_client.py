#
# Copyright (C) 2022 Northwestern University.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""DataCite DOI Client."""

from typing import Any
from unittest.mock import Mock

from idutils import normalize_doi
from invenio_rdm_records.services.pids import providers

type JSONDict = dict[str, Any]


class FakeDataCiteRESTClient:
    """DataCite REST API client wrapper."""

    def __init__(
        self,
        username,
        password,
        prefix,
        test_mode=False,
        url=None,
        timeout=None,
    ):
        """Initialize the REST client wrapper.

        :param username: DataCite username.
        :param password: DataCite password.
        :param prefix: DOI prefix (or CFG_DATACITE_DOI_PREFIX).
        :param test_mode: use test URL when True
        :param url: DataCite API base URL.
        :param timeout: Connect and read timeout in seconds. Specify a tuple
            (connect, read) to specify each timeout individually.
        """
        self.username = str(username)
        self.password = str(password)
        self.prefix = str(prefix)

        if test_mode:
            self.api_url = "https://api.test.datacite.org/"
        else:
            self.api_url = url or "https://api.datacite.org/"

        if not self.api_url.endswith("/"):
            self.api_url += "/"

        self.timeout = timeout

    def public_doi(
        self, metadata: JSONDict, url: str, doi: str | None = None
    ) -> Mock:
        """Create a public doi ... not.

        Arguments:
            metadata: JSON format of the metadata.
            doi: DOI (e.g. 10.123/456)
            url: URL where the doi will resolve.

        Returns:
            Mock placeholder for the public doi.
        """
        return Mock()

    def update_doi(
        self,
        doi: str,
        metadata: JSONDict | None = None,
        url: str | None = None,
    ) -> Mock:
        """Update the metadata or url for a DOI ... not.

        Arguments:
            doi: DOI (e.g. 10.123/456).
            url: URL where the doi will resolve.
            metadata: JSON format of the metadata.

        Returns:
            Mock placeholder for the updated DOI.
        """
        return Mock()

    def delete_doi(self, doi: str) -> Mock:
        """Delete a doi ... not.

        This will only work for draft dois

        Args:
            doi: DOI (e.g. 10.123/456).

        Returns:
            Mock placeholder for the deleted DOI.
        """
        return Mock()

    def hide_doi(self, doi: str) -> Mock:
        """Hide a previously registered DOI ... not.

        This DOI will no
        longer be found in DataCite Search

        Args:
            doi: DOI to hide, e.g. 10.12345/1.

        Returns:
            Mock placeholder for the hidden DOI.
        """
        return Mock()

    def show_doi(self, doi: str) -> Mock:
        """Show a previously hidden DOI ... not.

        This DOI will no
        longer be found in DataCite Search

        Args:
            doi: DOI to show, e.g. 10.12345/1.

        Returns:
            Mock placeholder for the shown DOI.
        """
        return Mock()

    def check_doi(self, doi: str) -> str:
        """Check doi structure.

        Check that the doi has a form
        12.12345/123 with the prefix defined

        Returns:
            The normalized DOI string.

        Raises:
            ValueError: If the DOI prefix does not match the configured prefix.
        """
        # If prefix is in doi
        if "/" in doi:
            split = doi.split("/")
            prefix = split[0]
            if prefix != self.prefix:
                # Provided a DOI with the wrong prefix
                raise ValueError(
                    f"Wrong DOI {prefix} prefix provided, it should be "
                    f"{self.prefix} as defined in the rest client"
                )
        else:
            doi = f"{self.prefix}/{doi}"
        return normalize_doi(doi)

    def __repr__(self) -> str:
        """Create a string representation of the object.

        Returns:
            The debug representation of the fake client.
        """
        return f"<FakeDataCiteRESTClient: {self.username}>"


class FakeDataCiteClient(providers.DataCiteClient):
    """Fake DataCite Client."""

    @property
    def api(self) -> FakeDataCiteRESTClient:
        """DataCite REST API client instance."""
        if self._api is None:
            self.check_credentials()
            self._api = FakeDataCiteRESTClient(
                self.cfg("username"),
                self.cfg("password"),
                self.cfg("prefix"),
                self.cfg("test_mode", True),
            )
        return self._api
