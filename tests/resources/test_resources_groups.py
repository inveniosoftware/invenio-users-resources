# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2025 KTH Royal Institute of Technology.
# Copyright (C) 2025 Northwestern University.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Groups resource tests."""


def test_group_create_api(app, client, user_moderator):
    user_moderator.login(client)

    payload = {
        "name": "api-role",
        "description": "Created via API",
        "is_managed": False,
    }

    res = client.post("/groups", json=payload)
    assert 201 == res.status_code
    data = res.get_json()
    assert payload["name"] == data["name"]
    assert payload["description"] == data["description"]

    res = client.delete(f"/groups/{data['id']}")
    assert 204 == res.status_code


def test_group_update_validation_error_api(app, client, user_moderator, group):
    """Invalid payloads should produce a clean JSON error."""
    user_moderator.login(client)

    invalid_description = "x" * 256

    res = client.put(
        f"/groups/{group.id}",
        json={"description": invalid_description},
    )

    assert 400 == res.status_code
    data = res.get_json()
    assert "A validation error occurred." == data["message"]
    assert data["errors"] == [
        {
            "field": "description",
            "messages": ["Longer than maximum length 255."],
        }
    ]


def test_group_update_requires_managed_api(
    app, client, user_moderator, not_managed_group
):
    """Unmanaged groups should return a friendly error."""
    user_moderator.login(client)

    res = client.put(
        f"/groups/{not_managed_group.id}",
        json={"description": "updated"},
    )

    assert 403 == res.status_code
    data = res.get_json()
    assert "Permission denied." == data["message"]
    assert "errors" not in data


def test_groups_search(app, client, group, user_moderator):
    user_moderator.login(client)

    res = client.get(f"/groups")

    assert res.status_code == 200
    data = res.json
    assert data["links"] == {
        "self": "https://127.0.0.1:5000/api/groups?page=1&size=20&sort=name"
    }


def test_groups_read(app, client, group, user_moderator):
    # Anonymous user forbidden
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
    # Anonymous user forbidden
    res = client.get(f"/groups/{not_managed_group.name}/avatar.svg")
    assert res.status_code == 403

    user_pub.login(client)

    # unmanaged group can be retrieved
    res = client.get(f"/groups/{not_managed_group.name}/avatar.svg")
    assert res.status_code == 200
    assert res.mimetype == "image/svg+xml"
    data = res.get_data()

    # managed group can *not* be retrieved
    res = client.get(f"/groups/{group.id}/avatar.svg")
    assert res.status_code == 403


# TODO: test conditional requests
# TODO: test caching headers
# TODO: test invalid identifiers
