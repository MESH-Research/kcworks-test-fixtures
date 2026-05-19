# Part of KCWorks Test Fixtures
#
# Copyright (C) 2025 MESH Research.
#
# KCWorks Test Fixtures is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Search provisioning related pytest fixtures for testing."""

import arrow
import pytest
from celery import shared_task

# Try to import the provisioner to detect if it's available
try:
    import invenio_remote_api_provisioner  # noqa: F401

    PROVISIONER_AVAILABLE = True
except ImportError:
    PROVISIONER_AVAILABLE = False


@shared_task(bind=True)
def mock_send_remote_api_update(
    self,
    identity_id: str = "",
    record: dict | None = None,
    is_published: bool = False,
    is_draft: bool = False,
    is_deleted: bool = False,
    parent: dict | None = None,
    latest_version_index: int | None = None,
    latest_version_id: str | None = None,
    current_version_index: int | None = None,
    draft: dict | None = None,
    endpoint: str = "",
    service_type: str = "",
    service_method: str = "",
    **kwargs,
):
    """Mock the send_remote_api_update task.

    Returns:
        tuple: A tuple of (response_text, callback_result) to match the real function.
    """
    record = record or {}
    if service_type == "rdm_record" and service_method == "publish":
        # Simulate a successful remote API update
        record["custom_fields"] = record.get("custom_fields", {})
        record["custom_fields"]["kcr:commons_search_recid"] = "2E9SqY0Bdd2QL-HGeUuA"
        record["custom_fields"]["kcr:commons_search_updated"] = arrow.utcnow().format(
            "YYYY-MM-DDTHH:mm:ssZ"
        )
    # Return a tuple of (response_text, callback_result) to match the real function
    return "OK", None


@pytest.fixture
def mock_send_remote_api_update_fixture(mocker):
    """Mock the sending of remote API updates.
    
    This fixture is context-aware:
    - If invenio_remote_api_provisioner is available, it patches the actual function
    - If not available, it's a no-op (for contexts where the dependency doesn't exist)
    """
    if PROVISIONER_AVAILABLE:
        mocker.patch(
            "invenio_remote_api_provisioner.components.send_remote_api_update",  # noqa: E501
            mock_send_remote_api_update,
        )
    # If provisioner is not available, this is a no-op fixture


@pytest.fixture
def mock_search_api_request(requests_mock):
    """Mock the sending of search API requests.

    Returns:
        function: Mock request function.
    """

    def mock_request(
        http_method: str,
        draft_id: str,
        metadata: dict,
        api_url: str,
    ):
        """Mock the sending of search API requests.

        Returns:
            dict: Mock response data.
        """
        mock_response = {
            "_internal_id": draft_id,
            "_id": "y-5ExZIBwjeO8JmmunDd",
            "title": metadata["metadata"]["title"],
            "description": metadata["metadata"].get("description", ""),
            "owner": {"url": "https://hcommons.org/profiles/myuser"},
            "contributors": [
                {
                    "name": (
                        f"{c['person_or_org'].get('family_name', '')}, "
                        f"{c['person_or_org'].get('given_name', '')}"
                    ),
                    "username": "user1",
                    "url": "https://hcommons.org/profiles/user1",
                    "role": "author",
                }
                for c in metadata["metadata"]["creators"]
            ],
            "primary_url": f"{api_url}/records/{draft_id}",
            "other_urls": [f"{api_url}/records/{draft_id}/files"],
            "publication_date": metadata["metadata"]["publication_date"],
            "modified_date": "2024-06-07",
            "content_type": "work",
            "network_node": "works",
        }
        mock_adapter = requests_mock.request(
            http_method,
            "https://search.hcommons-dev.org/v1/documents",
            json=mock_response,
        )  # noqa: E501
        return mock_adapter

    return mock_request


# TODO: This didn't work
# @pytest.fixture(scope="function")
# def mock_signal_subscriber(app, monkeypatch):
#     """Mock ext.on_api_provisioning_triggered event subscriber."""

#     def mocksubscriber(app_obj, *args, **kwargs):
#         with app_obj.app_context():
#             app_obj.logger.debug("Mocked remote_api_provisioning_triggered")
#             app_obj.logger.debug("Events:")
#             app_obj.logger(
#                 pformat(
#                     current_queues.queues[
#                         "remote-api-provisioning-events"
#                     ].events
#                 )
#             )
#             raise RuntimeError("Mocked remote_api_provisioning_triggered")

#     return mocksubscriber
