# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Domains resource tests."""

import pytest


def test_domains_access(app, client, domains, user_moderator, user_pub):
    res = client.get(f"/domains")
    assert res.status_code == 403

    user_pub.login(client)
    res = client.get(f"/domains")
    assert res.status_code == 403


def test_domains_search(app, client, domains, user_moderator, user_pub):
    user_moderator.login(client)
    res = client.get(f"/domains")
    assert res.status_code == 200
    data = res.json
    assert len(data["hits"]["hits"]) == 5

    # Props
    props = [
        "id",
        "domain",
        "created",
        "updated",
        "domain",
        "tld",
        "status",
        "status_name",
        "category",
        "category_name",
        "flagged",
        "flagged_source",
        "org",
        "num_users",
        "num_active",
        "num_inactive",
        "num_confirmed",
        "num_verified",
        "num_blocked",
    ]
    cern = data["hits"]["hits"][0]
    assert cern["domain"] == "cern.ch"
    for p in props:
        assert p in cern

    # Check aggregations and that they have content
    aggs = ["status", "flagged", "category", "organisation", "tld"]
    for a in aggs:
        assert a in data["aggregations"]
        assert (
            len(data["aggregations"][a]["buckets"]) > 0
        ), f"'{a}' is missing bucket values"
    assert len(data["hits"]["hits"]) == 5


def test_domains_read(app, client, domains, user_moderator):
    res = client.get(f"/domains/cern.ch")
    assert res.status_code == 403

    user_moderator.login(client)
    res = client.get(f"/domains/cern.ch")
    assert res.json["links"]["self"].endswith("/domains/cern.ch")
    assert res.status_code == 200
    d = res.json
    assert d["domain"] == "cern.ch"
    assert d["tld"] == "ch"
    assert d["status"] == 3
    assert d["status_name"] == "verified"
    assert d["flagged"] == False
    assert d["flagged_source"] == ""
    assert d["category"] == 1
    assert d["category_name"] == "organization"
    assert d["org"] == [
        {
            "id": 1,
            "pid": "https://ror.org/01ggx4157",
            "name": "CERN",
            "props": {"country": "ch"},
            "is_parent": False,
        }
    ]
    stats = ["users", "active", "inactive", "confirmed", "verified", "blocked"]
    for s in stats:
        assert f"num_{s}" in d, f"num_{s} is missing from payload"


def test_domains_delete(app, client, domains, user_moderator):
    res = client.delete(f"/domains/cern.ch")
    assert res.status_code == 403

    user_moderator.login(client)
    res = client.delete(f"/domains/cern.ch")
    assert res.status_code == 204
    res = client.get(f"/domains/cern.ch")
    assert res.status_code == 404


def test_domains_create(app, client, domains, user_moderator):
    res = client.post(
        f"/domains",
        json={
            "domain": "zenodo.org",
        },
        headers={"content-type": "application/vnd.inveniordm.v1+json"},
    )
    assert res.status_code == 403

    user_moderator.login(client)
    # Make an update
    res = client.post(
        f"/domains",
        json={
            "domain": "zenodo.org",
        },
        headers={"content-type": "application/vnd.inveniordm.v1+json"},
    )
    assert res.status_code == 201
    # Re-read to check that it was updated
    data = client.get(f"/domains/zenodo.org").json
    assert data["domain"] == "zenodo.org"
    assert data["tld"] == "org"
    assert data["status_name"] == "new"
    assert data["category_name"] == None
    assert data["flagged"] == False
    assert data["flagged_source"] == ""
    assert data["org"] is None


@pytest.mark.parametrize(
    "status_code,json",
    [
        (400, {"status": "new"}),  # missing domain
        (400, {"domain": "test.com", "status_name": "invalid"}),  # invalid status
        (400, {"domain": "spammer.com"}),  # duplicate domain
        (400, {"domain": "test.com", "category_name": "invalid"}),  # invalid category
    ],
)
def test_domains_create_failure(
    app, client, domains, user_moderator, status_code, json
):
    user_moderator.login(client)
    # Make an update
    res = client.post(
        f"/domains",
        json=json,
        headers={"content-type": "application/vnd.inveniordm.v1+json"},
    )
    assert res.status_code == status_code


def test_domains_update(app, client, domains, user_moderator):
    user_moderator.login(client)
    data = client.get(f"/domains/moderated.org").json
    assert data["domain"] == "moderated.org"
    assert data["status_name"] == "moderated"
    assert data["category_name"] == "mail-provider"
    assert data["flagged"] == True
    assert data["flagged_source"] == "disposable"
    assert data["org"] is None
    # Make an update
    res = client.put(
        f"/domains/moderated.org",
        json={
            "domain": "moderated.org",
            "status_name": "verified",
            "category_name": "spammer",
            "flagged": False,
            "flagged_source": "test",
            "org": None,
        },
        headers={"content-type": "application/vnd.inveniordm.v1+json"},
    )
    assert res.status_code == 200
    # Re-read to check that it was updated
    data = client.get(f"/domains/moderated.org").json
    assert data["domain"] == "moderated.org"
    assert data["tld"] == "org"
    assert data["status_name"] == "verified"
    assert data["category_name"] == "spammer"
    assert data["flagged"] == False
    assert data["flagged_source"] == "test"
    assert data["org"] is None
