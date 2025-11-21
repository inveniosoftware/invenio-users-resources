# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2025 Northwestern University.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Groups resource tests."""


def test_groups_search(app, client, group, user_moderator):
    user_moderator.login(client)

    res = client.get(f"/groups")

    assert res.status_code == 200
    data = res.json
    assert data["links"] == {
        "self": "https://127.0.0.1:5000/api/groups?facets=%7B%7D&page=1&size=10&sort=name"
    }


def test_groups_read(app, client, group, user_moderator):
    # Anonymous user forbiden
    res = client.get(f"/groups/{group.name}")
    assert res.status_code == 403

    # User moderator allowed
    client = user_moderator.login(client)
    res = client.get(f"/groups/{group.name}")
    assert res.status_code == 200
    d = res.json
    assert d["links"] == {
        "self": f"https://127.0.0.1:5000/api/groups/{group.id}",
        "avatar": f"https://127.0.0.1:5000/api/groups/{group.id}/avatar.svg",
    }


def test_group_avatar(app, client, group, not_managed_group, user_pub):
    # Anonymous user forbiden
    res = client.get(f"/groups/{not_managed_group.name}/avatar.svg")
    assert res.status_code == 403

    # unmanaged group can be retrieved
    user_pub.login(client)
    res = client.get(f"/groups/{not_managed_group.name}/avatar.svg")
    assert res.status_code == 200
    assert res.mimetype == "image/svg+xml"

    # managed group can *not* be retrieved
    res = client.get(f"/groups/{group.name}/avatar.svg")
    assert res.status_code == 403


# TODO: test conditional requests
# TODO: test caching headers
# TODO: test invalid identifiers
