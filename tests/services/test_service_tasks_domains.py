# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

from unittest.mock import MagicMock, patch

from invenio_access.permissions import system_identity

from invenio_users_resources.services.domains.tasks import import_domain_blocklist


@patch("invenio_users_resources.services.domains.tasks.requests.get")
def test_import_domain_blocklist(
    mock_get, app, db, domains, domains_service, clear_cache
):
    # Mock the response from requests.get
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"spamdomain.com.\nnew.org\n"
    mock_get.return_value = mock_resp

    domain = domains_service.read(system_identity, "new.org")
    assert domain.data["domain"] == "new.org"
    assert domain.data["status_name"] == "new"
    assert domain.data["flagged"] is False

    # Call the task
    import_domain_blocklist("http://fake-url", "testsource")

    domain = domains_service.read(system_identity, "spamdomain.com")
    assert domain.data["domain"] == "spamdomain.com"
    assert domain.data["status_name"] == "blocked"
    assert domain.data["flagged"] is True
    assert domain.data["flagged_source"] == "testsource"

    # new.org is defined in fixtures and already exists.
    domain = domains_service.read(system_identity, "new.org")
    assert domain.data["domain"] == "new.org"
    assert domain.data["status_name"] == "new"
    assert domain.data["flagged"] is True
    assert domain.data["flagged_source"] == "testsource"


@patch("invenio_users_resources.services.domains.tasks.requests.get")
def test_import_domain_blocklist_download_error(
    mock_get, app, db, domains, domains_service, clear_cache
):
    # Mock the response from requests.get
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_get.return_value = mock_resp

    # Call the task
    import_domain_blocklist("http://fake-url", "testsource")
