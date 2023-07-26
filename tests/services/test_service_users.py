# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User service tests."""

import pytest
from invenio_access.permissions import system_identity
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


def test_search_permissions(app, db, user_service, user_moderator, user_res):
    """Test service search for permissions."""
    # User can search for himself
    search = user_service.search(
        user_res.identity, q=f"username:{user_res._user.username}"
    )
    assert search.total > 0

    # User can't search for non-confirmed users
    with pytest.raises(PermissionDeniedError):
        user_service.search_all(user_res.identity, user_res.id)

    # Moderator can search for any user
    search = user_service.search_all(
        user_moderator.identity, q=f"username:{user_res._user.username}"
    )
    assert search.total > 0


def test_block(app, db, user_service, user_moderator, user_res):
    """Test user block."""

    with pytest.raises(PermissionDeniedError):
        user_service.block(user_res.identity, user_res.id)

    blocked = user_service.block(user_moderator.identity, user_res.id)
    assert blocked

    ur = user_service.read(user_res.identity, user_res.id)
    # User can't see when it was blocked
    assert not "blocked_at" in ur.data
    # But can see it's not active
    assert ur.data["active"] is False

    ur = user_service.read(user_moderator.identity, user_res.id)
    # Moderator can see the blocked_at time
    assert ur.data["blocked_at"] is not None

    # TODO user is blocked, the user should not be able to search.
    # search = user_service.search(user_res.identity, q=f"username:{ur._user.username}")
    # assert search.total == 0

    # Moderator can still search for the user
    search = user_service.search_all(
        user_moderator.identity, q=f"username:{user_res._user.username}"
    )
    assert search.total > 0


def test_approve(user_service, user_res, user_moderator):
    """Test approval of an user."""
    with pytest.raises(PermissionDeniedError):
        user_service.block(user_res.identity, user_res.id)

    approved = user_service.approve(user_moderator.identity, user_res.id)
    assert approved

    ur = user_service.read(user_res.identity, user_res.id)
    # User can't see when it was approved
    assert not "verified_at" in ur.data
    # But can see it's active
    assert ur.data["active"] is True

    ur = user_service.read(user_moderator.identity, user_res.id)
    # Moderator can see when it was approved
    assert "verified_at" in ur.data


def test_deactivate(user_service, user_res, user_moderator):
    """Test deactivation of an user."""
    with pytest.raises(PermissionDeniedError):
        user_service.block(user_res.identity, user_res.id)

    deactivated = user_service.deactivate(user_moderator.identity, user_res.id)
    assert deactivated

    ur = user_service.read(user_res.identity, user_res.id)
    # User can see it's not active
    assert ur.data["active"] is False

    # Moderator can still search for the user
    search = user_service.search_all(
        user_moderator.identity, q=f"username:{user_res._user.username}"
    )
    assert search.total > 0
