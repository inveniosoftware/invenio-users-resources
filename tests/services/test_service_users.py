# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User service tests."""

import pytest
from invenio_records_resources.services.errors import PermissionDeniedError


#
# Search
#
def test_search_restricted(user_service, anon_identity, user_pub):
    """Only authenticated users can search."""
    # Anon identity
    pytest.raises(
        # TODO: Should be mapped to a 404
        PermissionDeniedError,
        user_service.search,
        anon_identity,
    )
    # Authenticated identity
    res = user_service.search(user_pub.identity).to_dict()
    assert res["hits"]["total"] > 0


def test_search_public_users(user_service, user_pub):
    """Only public users are shown in search."""
    res = user_service.search(user_pub.identity).to_dict()
    assert res["hits"]["total"] == 2  # 2 public users in conftest


@pytest.mark.parametrize(
    "query",
    [
        "email:res@inveniosoftware.org",
        "res@inveniosoftware.org",
        "email:pubres@inveniosoftware.org",
        "pubres@inveniosoftware.org",
        "Plazi",
        "+name:Jose -affiliation:CERN",
        "name:Jose AND NOT affiliation:CERN",
        "username:inactive",
        "username:unconfirmed",
        "preferences.visibility:public",
        "preferences.email_visibility:restricted",
        "profile.affiliations:Plazi",
        "invalid:test",
    ],
)
def test_search_field_not_searchable(user_service, user_pub, query):
    """Make sure certain fields are NOT searchable."""
    res = user_service.search(user_pub.identity, q=query).to_dict()
    assert res["hits"]["total"] == 0


@pytest.mark.parametrize(
    "query",
    [
        "affiliations:CERN",
        "affiliation:CERN",
        "name:Jose affiliation:CERN",
        "+name:Jose +affiliation:CERN",
        "CERN",
        "Tim",
        "Tim CERN",
        "Jose",
        "Jose CERN",
        "email:pub@inveniosoftware.org",
        "username:pub",
    ],
)
def test_search_field(user_service, user_pub, query):
    """Make sure certain fields ARE searchable."""
    res = user_service.search(user_pub.identity, q=query).to_dict()
    assert res["hits"]["total"] > 0


#
# Read
#
def test_read_with_anon(user_service, anon_identity, user_pub, user_pubres, user_res):
    """Anonymous users can read a single *public* user."""
    res = user_service.read(anon_identity, user_pub.id).to_dict()
    assert res["username"] == "pub"
    assert res["email"] == user_pub.email
    res = user_service.read(anon_identity, user_pubres.id).to_dict()
    assert res["username"] == "pubres"
    assert "email" not in res
    pytest.raises(
        # TODO: Should be mapped to a 404
        PermissionDeniedError,
        user_service.read,
        anon_identity,
        user_res.id,
    )


@pytest.mark.parametrize(
    "username,can_read", [("pub", True), ("pubres", True), ("res", False)]
)
def test_read_avatar_with_anon(user_service, anon_identity, users, username, can_read):
    """Anonymous users can read avatar single *public* user."""
    user = users[username]
    if can_read:
        user_service.read_avatar(anon_identity, user.id)
    else:
        pytest.raises(
            # TODO: Should be mapped to a 404
            PermissionDeniedError,
            user_service.read_avatar,
            anon_identity,
            user.id,
        )


@pytest.mark.parametrize(
    "username",
    [
        "pub",
        "pubres",
        "res",
    ],
)
def test_read_self(user_service, users, username):
    """Users can read themselves."""
    user = users[username]
    res = user_service.read(user.identity, user.id).to_dict()
    assert res["username"] == username
    # Email can be seen even if restricted
    assert res["email"] == user.email
    # Avatar can also be seen.
    user_service.read_avatar(user.identity, user.id)
