# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2026 CERN.
# Copyright (C) 2024 Ubiquity Press.
# Copyright (C) 2026 KTH Royal Institute of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User service tests."""

import pytest
from invenio_access.permissions import system_identity
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


def test_admin_search_filter_and_facet_roles(
    user_service, user_moderator, user_pub, group
):
    """Admin search can filter/facet users by roles."""
    user_service.add_group(user_moderator.identity, user_pub.id, "it-dep")
    res = user_service.search_all(user_moderator.identity, q="roles:it-dep").to_dict()
    assert str(user_pub.id) in [hit["id"] for hit in res["hits"]["hits"]]
    assert "aggregations" in res
    assert "roles" in res["aggregations"]


def test_admin_roles_facet_size_configured(app):
    """Roles facet should return many buckets, not just the default 10."""
    roles_facet_config = app.config["USERS_RESOURCES_SEARCH_FACETS"]["roles"]
    assert roles_facet_config["facet_options"]["size"] == 100


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


USERNAME_JOSE = ["pub"]
USERNAME_TIM = ["pub-res"]
USERNAME_BOTH = USERNAME_JOSE + USERNAME_TIM


#
# Read
@pytest.mark.parametrize(
    "query,expected_usernames",
    [
        ("CERN", USERNAME_BOTH),
        ("Jose", USERNAME_JOSE),
        ("Jos", USERNAME_JOSE),
        ("Jose CERN", USERNAME_JOSE),
        ("Tim", USERNAME_TIM),
        ("Tim CERN", USERNAME_TIM),
        ("pub@inveniosoftware.org", USERNAME_JOSE),
        ("pub@inveniosoftware.or", USERNAME_JOSE),
        ("pub", USERNAME_BOTH),
        ("pub-res", USERNAME_TIM),
        ("re", USERNAME_TIM),
        ("res", USERNAME_TIM),
    ],
)
def test_user_search_field(user_service, user_pub, query, expected_usernames):
    """Make sure certain fields ARE searchable."""
    res = user_service.search(user_pub.identity, suggest=query).to_dict()
    usernames = [entry["username"] for entry in res["hits"]["hits"]]
    assert sorted(usernames) == expected_usernames


#
# Read
#
def test_read_with_anon(user_service, anon_identity, user_pub, user_pubres, user_res):
    """Anonymous users cannot read/read_avatar a single user."""
    pytest.raises(PermissionDeniedError, user_service.read, anon_identity, user_pub.id)
    pytest.raises(
        PermissionDeniedError, user_service.read_avatar, anon_identity, user_pub.id
    )
    pytest.raises(
        PermissionDeniedError, user_service.read, anon_identity, user_pubres.id
    )
    pytest.raises(
        PermissionDeniedError, user_service.read_avatar, anon_identity, user_pubres.id
    )
    pytest.raises(PermissionDeniedError, user_service.read, anon_identity, user_res.id)
    pytest.raises(
        PermissionDeniedError, user_service.read_avatar, anon_identity, user_res.id
    )


def test_read_with_logged_in(
    user_service, auth_identity, user_accented, user_pub, user_pubres, user_res
):
    """Logged in users can read public users only."""
    random_identity = auth_identity(user_accented.id)
    res = user_service.read(random_identity, user_pub.id).to_dict()
    assert res["username"] == "pub"
    assert res["email"] == user_pub.email
    user_service.read_avatar(random_identity, user_pub.id)

    res = user_service.read(random_identity, user_pubres.id).to_dict()
    assert res["username"] == "pub-res"
    assert "email" not in res
    user_service.read_avatar(random_identity, user_pubres.id)

    pytest.raises(
        PermissionDeniedError,
        user_service.read,
        random_identity,
        user_res.id,
    )
    pytest.raises(
        PermissionDeniedError,
        user_service.read_avatar,
        random_identity,
        user_res.id,
    )


@pytest.mark.parametrize(
    "username",
    [
        "pub",
        "pub-res",
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
        "username": [
            "Username must start with a letter, be at least three characters long "
            "and only contain alphanumeric characters, dashes and underscores.",
        ],
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
    assert exc_info.value.messages == {
        "username": [
            "Username must start with a letter, be at least three "
            "characters long and only contain alphanumeric characters, dashes and "
            "underscores."
        ],
    }
    # Invalid values for username with non alpha, dash or underscore
    with pytest.raises(ValidationError) as exc_info:
        user_service.create(
            user_moderator.identity,
            {
                "username": "aaaa_1-:",
                "email": "valid@up.com",
            },
        )
    assert exc_info.value.messages == {
        "username": [
            "Username must start with a letter, be at least three "
            "characters long and only contain alphanumeric characters, dashes and "
            "underscores."
        ],
    }
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
    assert ur.data["active"] is False
    assert ur.data["blocked_at"] is not None

    restored = user_service.restore(user_moderator.identity, user_res.id)
    assert restored

    ur = user_service.read(user_moderator.identity, user_res.id)
    assert ur.data["active"] is True
    assert ur.data["confirmed_at"] is not None
    assert ur.data["verified_at"] is None
    assert ur.data["blocked_at"] is None


def test_can_impersonate_user(
    app, db, user_service, user_pub, user_moderator, user_admin
):
    """Test permissions on user impersonate."""
    with pytest.raises(PermissionDeniedError):
        user_service.can_impersonate(user_pub.identity, user_moderator.id)

    assert user_service.can_impersonate(user_moderator.identity, user_pub.id)
    with pytest.raises(PermissionDeniedError):
        assert user_service.can_impersonate(user_moderator.identity, user_admin.id)

    assert user_service.can_impersonate(user_admin.identity, user_pub.id)
    assert user_service.can_impersonate(user_admin.identity, user_moderator.id)


# TODO Clear the cache to test actions without locking side-effects


def test_add_group_normalizes_role_id(user_service, user_moderator, user_pub, group):
    """Role IDs are normalized at service boundary."""
    assert user_service.add_group(user_moderator.identity, user_pub.id, "  it-dep  ")
    groups = user_service.get_groups(user_moderator.identity, user_pub.id)["groups"]
    assert "it-dep" in [group["id"] for group in groups]


def test_add_group_empty_role_id_validation(user_service, user_moderator, user_pub):
    """Empty/blank role IDs fail with validation error."""
    with pytest.raises(ValidationError):
        user_service.add_group(user_moderator.identity, user_pub.id, "   ")


def test_add_group_self_forbidden(user_service, user_moderator):
    """Self role mutation is denied via manage_groups + PreventSelf."""
    with pytest.raises(PermissionDeniedError):
        user_service.add_group(user_moderator.identity, user_moderator.id, "it-dep")


def test_add_group_unknown_role_validation(user_service, user_moderator, user_pub):
    """Unknown role IDs are denied to avoid role enumeration."""
    with pytest.raises(PermissionDeniedError):
        user_service.add_group(user_moderator.identity, user_pub.id, "unknown-role-id")


def test_remove_group_noop_when_role_missing(user_service, user_moderator, user_pub):
    """Removing a non-member role is a no-op."""
    assert user_service.remove_group(user_moderator.identity, user_pub.id, "it-dep")


def test_set_groups_add_remove_mixed(
    user_service, user_moderator, user_pub, group, group2
):
    """Bulk replacement adds and removes groups in one operation."""
    user_service.set_groups(user_moderator.identity, user_pub.id, ["it-dep"])

    result = user_service.set_groups(
        user_moderator.identity,
        user_pub.id,
        ["hr-dep"],
    )

    assert result == {
        "added": ["hr-dep"],
        "removed": ["it-dep"],
        "groups": ["hr-dep"],
    }


def test_add_groups_additive_no_removal(
    user_service, user_moderator, user_pub, group, group2
):
    """Bulk add appends roles without removing existing memberships."""
    user_service.set_groups(user_moderator.identity, user_pub.id, ["it-dep"])

    result = user_service.add_groups(
        user_moderator.identity,
        user_pub.id,
        ["it-dep", "hr-dep"],
    )

    assert result == {
        "added": ["hr-dep"],
        "removed": [],
        "groups": ["hr-dep", "it-dep"],
    }


def test_set_groups_noop(user_service, user_moderator, user_pub, group):
    """Bulk replacement is a no-op if requested roles are unchanged."""
    user_service.set_groups(user_moderator.identity, user_pub.id, ["it-dep"])

    result = user_service.set_groups(
        user_moderator.identity,
        user_pub.id,
        ["it-dep"],
    )

    assert result == {
        "added": [],
        "removed": [],
        "groups": ["it-dep"],
    }


def test_set_groups_normalizes_whitespace(
    user_service, user_moderator, user_pub, group, group2
):
    """Bulk replacement normalizes IDs and ignores blanks."""
    user_service.set_groups(user_moderator.identity, user_pub.id, [])

    result = user_service.set_groups(
        user_moderator.identity,
        user_pub.id,
        ["  it-dep  ", " ", "\thr-dep\t"],
    )

    assert result == {
        "added": ["hr-dep", "it-dep"],
        "removed": [],
        "groups": ["hr-dep", "it-dep"],
    }


def test_set_groups_empty_clears_mutable_roles(
    user_service, user_moderator, user_pub, group, group2
):
    """Bulk replacement with [] clears all mutable roles."""
    user_service.set_groups(user_moderator.identity, user_pub.id, ["it-dep", "hr-dep"])

    result = user_service.set_groups(
        user_moderator.identity,
        user_pub.id,
        [],
    )

    assert result == {
        "added": [],
        "removed": ["hr-dep", "it-dep"],
        "groups": [],
    }


def test_set_groups_unknown_role_validation(user_service, user_moderator, user_pub):
    """Unknown role IDs are denied to avoid role enumeration."""
    with pytest.raises(PermissionDeniedError):
        user_service.set_groups(
            user_moderator.identity,
            user_pub.id,
            ["unknown-role-id"],
        )


def test_set_groups_self_forbidden(user_service, user_moderator, group):
    """Self role mutation is denied in bulk endpoint too."""
    with pytest.raises(PermissionDeniedError):
        user_service.set_groups(user_moderator.identity, user_moderator.id, ["it-dep"])


def test_get_groups_self_allowed(user_service, user_moderator):
    """Users can read their own role list."""
    result = user_service.get_groups(user_moderator.identity, user_moderator.id)
    assert "groups" in result
    assert "total" in result


def test_get_groups_other_user_permission_denied(user_service, user_pub, user_res):
    """Non-managers cannot read role list of other users."""
    with pytest.raises(PermissionDeniedError):
        user_service.get_groups(user_pub.identity, user_res.id)


def test_set_groups_permission_denied(user_service, user_pub, user_res, group):
    """Non-managers cannot mutate groups of other users."""
    with pytest.raises(PermissionDeniedError):
        user_service.set_groups(user_pub.identity, user_res.id, ["it-dep"])


def test_remove_groups_bulk(user_service, user_moderator, user_pub, group, group2):
    """Bulk remove deletes only requested assigned roles."""
    user_service.set_groups(
        user_moderator.identity,
        user_pub.id,
        ["it-dep", "hr-dep"],
    )

    result = user_service.remove_groups(
        user_moderator.identity,
        user_pub.id,
        ["it-dep"],
    )

    assert result == {
        "added": [],
        "removed": ["it-dep"],
        "groups": ["hr-dep"],
    }


def test_remove_groups_unknown_role_denied(user_service, user_moderator, user_pub):
    """Unknown role IDs are denied in bulk remove too."""
    with pytest.raises(PermissionDeniedError):
        user_service.remove_groups(
            user_moderator.identity,
            user_pub.id,
            ["unknown-role-id"],
        )


def test_remove_groups_self_forbidden(user_service, user_moderator, group):
    """Self bulk role removal is denied."""
    with pytest.raises(PermissionDeniedError):
        user_service.remove_groups(
            user_moderator.identity, user_moderator.id, ["it-dep"]
        )


def test_set_groups_protected_role_allowed(
    app, user_service, user_moderator, user_pub, user_res, group
):
    """Protected roles can be managed through user-role assignment endpoints."""
    user_service.set_groups(user_moderator.identity, user_pub.id, ["it-dep"])

    previous = app.config.get("USERS_RESOURCES_PROTECTED_GROUP_NAMES", [])
    app.config["USERS_RESOURCES_PROTECTED_GROUP_NAMES"] = ["it-dep"]
    try:
        result_remove = user_service.set_groups(
            user_moderator.identity, user_pub.id, []
        )
        assert result_remove["removed"] == ["it-dep"]
        result_add = user_service.set_groups(
            user_moderator.identity, user_res.id, ["it-dep"]
        )
        assert result_add["added"] == ["it-dep"]
    finally:
        app.config["USERS_RESOURCES_PROTECTED_GROUP_NAMES"] = previous


def test_remove_protected_role_allowed_for_superadmin(
    app, user_service, user_admin, user_pub
):
    """Superadmins can remove protected roles on other users."""
    previous = app.config.get("USERS_RESOURCES_PROTECTED_GROUP_NAMES", [])
    app.config["USERS_RESOURCES_PROTECTED_GROUP_NAMES"] = ["admin"]
    try:
        user_service.add_group(system_identity, user_pub.id, "admin")
        assert user_service.remove_group(user_admin.identity, user_pub.id, "admin")
    finally:
        app.config["USERS_RESOURCES_PROTECTED_GROUP_NAMES"] = previous


def test_add_protected_role_allowed_for_superadmin(
    app, user_service, user_admin, user_pub
):
    """Superadmins can add protected roles on other users."""
    previous = app.config.get("USERS_RESOURCES_PROTECTED_GROUP_NAMES", [])
    app.config["USERS_RESOURCES_PROTECTED_GROUP_NAMES"] = ["admin"]
    try:
        assert user_service.add_group(user_admin.identity, user_pub.id, "admin")
    finally:
        user_service.remove_group(system_identity, user_pub.id, "admin")
        app.config["USERS_RESOURCES_PROTECTED_GROUP_NAMES"] = previous
