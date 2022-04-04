# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 European Union.
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User resource tests."""

import pytest


#
# Read
#
def test_read_self_serialization(client, headers, users, user_pub):
    """Read self user."""
    client = user_pub.login(client)
    r = client.get(f"/users/{user_pub.id}", headers=headers)
    assert r.status_code == 200
    data = r.json
    assert data["id"] == user_pub.id
    assert isinstance(data["id"], str)  # must be a string and not an integer
    assert data["email"] == user_pub.email
    assert data["username"] == user_pub.username
    assert data["is_current_user"] is True
    assert data["active"] is True
    assert data["confirmed"] is True
    assert data["profile"] == {
        "full_name": "Jose Benito Gonzalez Lopez",
        "affiliations": "CERN",
    }
    assert data["preferences"] == {"email_visibility": "public", "visibility": "public"}
    assert "created" in data
    assert "updated" in data
    assert "revision_id" in data
    assert data["links"] == {
        "self": f"https://127.0.0.1:5000/api/users/{user_pub.id}",
        "avatar": f"https://127.0.0.1:5000/api/users/{user_pub.id}/avatar.svg",
    }


@pytest.mark.parametrize(
    "username,public_email",
    [("pub", True), ("pubres", False)],
)
def test_read_anon_serialization(client, headers, users, username, public_email):
    """Read public user as anon."""
    u = users[username]
    # No login
    r = client.get(f"/users/{u.id}", headers=headers)
    assert r.status_code == 200

    data = r.json
    assert data["id"] == u.id
    assert isinstance(data["id"], str)  # must be a string and not an integer
    if public_email:
        assert data["email"] == u.email
    else:
        assert "email" not in data
    assert data["username"] == u.username
    assert data["is_current_user"] is False
    assert data["profile"] == {
        "full_name": u.user.user_profile["full_name"],
        "affiliations": u.user.user_profile["affiliations"],
    }
    assert data["links"] == {
        "self": f"https://127.0.0.1:5000/api/users/{u.id}",
        "avatar": f"https://127.0.0.1:5000/api/users/{u.id}/avatar.svg",
    }

    for k in [
        "active",
        "confirmed",
        "preferences",
        "created",
        "updated",
        "revision_id",
    ]:
        assert k not in data


#
# Avatar
#
def test_user_avatar(client, user_pub):
    res = client.get(f"/users/{user_pub.id}/avatar.svg")
    assert res.status_code == 200
    assert res.mimetype == "image/svg+xml"
    data = res.get_data()


# TODO: test conditional requests
# TODO: test caching headers
# TODO: test invalid identifiers
