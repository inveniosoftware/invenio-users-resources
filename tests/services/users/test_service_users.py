# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2024 Ubiquity Press.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User service tests."""

import pytest
from invenio_records_resources.services.errors import PermissionDeniedError
from marshmallow import ValidationError

from invenio_users_resources.proxies import current_actions_registry


@pytest.fixture(scope="function", autouse=True)
def mock_action_registry(monkeypatch, user_service):
    """Mocks action to registry entirely.

    Monkeypatches the registry to be modified only for testing.
    """

    for key in current_actions_registry:
        monkeypatch.setitem(current_actions_registry, key, [])
    return True


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


# Admin search
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
        "Jos",
        "Jose CERN",
        "email:pub@inveniosoftware.org",
        "username:pub",
    ],
)
def test_admin_search_field(user_service, user_moderator, query):
    """Make sure certain fields ARE searchable."""
    res = user_service.search_all(user_moderator.identity, q=query).to_dict()
    assert res["hits"]["total"] > 0


# User search
@pytest.mark.parametrize(
    "query",
    [
        "res@inveniosoftware.org",
        "pubres@inveniosoftware.org",
        "Plazi",
        "inactive",
        "unconfirmed",
        "restricted",
        "Plazi",
        "test",
    ],
)
def test_user_search_field_not_searchable(user_service, user_pub, query):
    """Make sure certain fields are NOT searchable."""
    res = user_service.search(user_pub.identity, suggest=query).to_dict()
    assert res["hits"]["total"] == 0


@pytest.mark.parametrize(
    "query",
    [
        "CERN",
        "Jose CERN",
        "Jose AND CERN",
        "Tim",
        "Tim CERN",
        "Jose",
        "Jos",
        "pub@inveniosoftware.org",
        "pub",
    ],
)
def test_user_search_field(user_service, user_pub, query):
    """Make sure certain fields ARE searchable."""
    res = user_service.search(user_pub.identity, suggest=query).to_dict()
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
        user_res.identity,
        q=user_res._user.username,
        fields=["username"],
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


def test_create_permission_denied(
    app, db, user_service, user_moderator, user_res, clear_cache, search_clear
):
    """Test user create permission denied."""
    data = {
        "username": "newuser",
        "email": "newuser@inveniosoftware.org",
    }

    with pytest.raises(PermissionDeniedError):
        user_service.create(user_res.identity, data)


def test_create_user(
    app, db, user_service, user_moderator, user_res, clear_cache, search_clear
):
    """Test user create."""
    data = {
        "username": "newuser",
        "email": "newuser@inveniosoftware.org",
    }
    res = user_service.create(user_moderator.identity, data).to_dict()

    ur = user_service.read(user_moderator.identity, res["id"])
    # Make sure new user is active and verified
    assert ur.data["username"] == "newuser"
    assert ur.data["active"]
    assert ur.data["verified"]

    # Invalid as no email
    with pytest.raises(ValidationError) as exc_info:
        user_service.create(
            user_moderator.identity,
            {"email": None},
        )
    assert exc_info.value.messages == {"email": ["Missing data for required field."]}


def test_create_user_errors(
    app, db, user_service, user_moderator, user_res, clear_cache, search_clear
):
    """Test user create errors."""
    # Invalid values
    with pytest.raises(ValidationError) as exc_info:
        user_service.create(
            user_moderator.identity,
            {
                "username": "a",
                "email": "invalid",
            },
        )
    assert exc_info.value.messages == {
        "email": ["Not a valid email address."],
    }

    # Invalid values for username not starting with alpha
    with pytest.raises(ValidationError) as exc_info:
        user_service.create(
            user_moderator.identity,
            {
                "username": "_aaa",
                "email": "valid@up.com",
            },
        )
    assert exc_info.value.messages == [
        "Unexpected Issue: Username must start with a letter, be at least three "
        "characters long and only contain alphanumeric characters, dashes and "
        "underscores.",
    ]

    # Invalid values for username with non alpha, dash or underscore
    with pytest.raises(ValidationError) as exc_info:
        user_service.create(
            user_moderator.identity,
            {
                "username": "aaaa_1-:",
                "email": "valid@up.com",
            },
        )
    assert exc_info.value.messages == [
        "Unexpected Issue: Username must start with a letter, be at least three "
        "characters long and only contain alphanumeric characters, dashes and "
        "underscores.",
    ]

    data = {
        "username": "newuser",
        "email": "newuser@inveniosoftware.org",
    }
    user_service.create(user_moderator.identity, data).to_dict()
    # Cannot re-add same details for new user
    with pytest.raises(ValidationError) as exc_info:
        user_service.create(user_moderator.identity, data)

    assert exc_info.value.messages == {
        "username": ["Username already used by another account."],
        "email": ["Email already used by another account."],
    }


def test_block(
    app, db, user_service, user_moderator, user_res, clear_cache, search_clear
):
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


def test_approve(
    app, db, user_service, user_res, user_moderator, clear_cache, search_clear
):
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


def test_deactivate(app, db, user_service, user_res, user_moderator, clear_cache):
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


def test_non_existent_user_management(app, db, user_service, user_moderator):
    """Try to manage a non-existent user."""
    fake_user_id = 1000
    funcs = [
        user_service.block,
        user_service.approve,
        user_service.deactivate,
        user_service.restore,
    ]
    for f in funcs:
        with pytest.raises(PermissionDeniedError):
            f(user_moderator.identity, fake_user_id)


def test_restore(app, db, user_service, user_res, user_moderator, clear_cache):
    """Test restore of a user."""
    blocked = user_service.block(user_moderator.identity, user_res.id)
    assert blocked

    ur = user_service.read(user_moderator.identity, user_res.id)
    assert ur.data["active"] == False
    assert ur.data["blocked_at"] is not None

    restored = user_service.restore(user_moderator.identity, user_res.id)
    assert restored

    ur = user_service.read(user_moderator.identity, user_res.id)
    assert ur.data["active"] == True
    assert ur.data["confirmed_at"] is not None
    assert ur.data["verified_at"] is None
    assert ur.data["blocked_at"] is None


# TODO Clear the cache to test actions without locking side-effects
