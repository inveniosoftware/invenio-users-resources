# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User service tests."""

from operator import attrgetter
import pytest
from invenio_access.permissions import system_identity
from invenio_records_resources.resources.errors import PermissionDeniedError
from marshmallow import ValidationError


def test_groups_sort(app, groups, group_service):
    """Test default sort."""
    sorted_groups = sorted(groups, key=attrgetter("name"))
    res = group_service.search(system_identity).to_dict()
    assert res["sortBy"] == "name"
    assert res["hits"]["total"] > 0
    hits = res["hits"]["hits"]
    assert hits[0]["id"] == sorted_groups[0].id
    assert hits[1]["id"] == sorted_groups[1].id
    for hit in hits:
        # FIXME: this probably doesn't make sense anymore
        assert hit["id"] == hit["name"]


def test_groups_no_facets(app, group, group_service):
    """Make sure certain fields ARE searchable."""
    res = group_service.search(system_identity)
    # if facets were enabled but not configured the value would be {}
    assert res.aggregations is None


def test_groups_fixed_pagination(app, groups, group_service):
    res = group_service.search(system_identity, params={"size": 1, "page": 2})
    assert res.pagination.page == 1
    assert res.pagination.size == 10


@pytest.mark.parametrize(
    "query",
    [
        # cannot search on title because is never set
        # see TODO in parse_role_data
        "id:it-dep",
        "name:IT Department",
        "+name:it",
        "IT",
    ],
)
def test_groups_search_field(app, group, group_service, query):
    """Make sure certain fields ARE searchable."""
    res = group_service.search(system_identity, q=query)
    assert res.total > 0


def test_groups_search(
    app, groups, group_service, user_pub, user_admin, user_moderator, anon_identity
):
    """Test group search."""

    # System can retrieve all groups.
    res = group_service.search(system_identity).to_dict()
    assert res["hits"]["total"] == len(groups)

    # Authenticated user can retrieve unmanaged groups
    res = group_service.search(user_pub.identity).to_dict()
    assert res["hits"]["total"] == len([g for g in groups if not g.is_managed])

    # Super Admin can see everything
    res = group_service.search(user_admin.identity).to_dict()
    assert res["hits"]["total"] == len(groups)

    # User Admin can see everything but admin groups
    res = group_service.search(user_moderator.identity).to_dict()
    assert res["hits"]["total"] == len(groups) - 1  # There is one superadmin group

    # Anon does not have permission to search
    with pytest.raises(PermissionDeniedError):
        group_service.search(anon_identity).to_dict()


def test_groups_read(
    app, groups, group_service, user_admin, user_moderator, user_pub, anon_identity
):
    """Test group read."""
    *regular_groups, superadmin_group = groups
    for g in regular_groups:
        # System can retrieve all groups.
        group_service.read(system_identity, g.id).to_dict()
        # Super admin can retrieve all groups
        group_service.read(user_admin.identity, g.id).to_dict()
        # User moderator can retrieve all groups
        group_service.read(user_moderator.identity, g.id).to_dict()
        # Authenticated user can retrieve unmanaged groups
        if g.is_managed:
            with pytest.raises(PermissionDeniedError):
                group_service.read(user_pub.identity, g.id).to_dict()
        else:
            group_service.read(user_pub.identity, g.id).to_dict()

        # Anon does not have permission to search
        with pytest.raises(PermissionDeniedError):
            group_service.read(anon_identity, g.id).to_dict()

    # System user
    group_service.read(system_identity, superadmin_group.id).to_dict()
    # Super user
    group_service.read(user_admin.identity, superadmin_group.id)
    # User moderator
    with pytest.raises(PermissionDeniedError):
        group_service.read(user_pub.identity, superadmin_group.id)
    # Authenicated user
    with pytest.raises(PermissionDeniedError):
        group_service.read(user_moderator.identity, superadmin_group.id)
    with pytest.raises(PermissionDeniedError):
        group_service.read(anon_identity, superadmin_group.id)


def test_groups_crud(app, group_service, user_pub):
    """Test creating, updating and deleting a group by name."""

    payload = {
        "name": "test-role",
        "description": "Initial description",
    }

    item = group_service.create(system_identity, payload).to_dict()
    assert item["id"] == payload["name"]
    assert item["name"] == payload["name"]
    assert item["description"] == payload["description"]

    with pytest.raises(PermissionDeniedError):
        group_service.create(user_pub.identity, {"name": "another-role"})

    updated = group_service.update(
        system_identity,
        payload["name"],
        {"description": "Updated"},
    ).to_dict()
    assert updated["description"] == "Updated"

    with pytest.raises(ValidationError):
        group_service.update(
            system_identity,
            payload["name"],
            {"name": "another"},
        )

    with pytest.raises(PermissionDeniedError):
        group_service.update(
            user_pub.identity,
            payload["name"],
            {"description": "Nope"},
        )

    with pytest.raises(PermissionDeniedError):
        group_service.delete(user_pub.identity, payload["name"])

    assert group_service.delete(system_identity, payload["name"])

    with pytest.raises(PermissionDeniedError):
        group_service.read(system_identity, payload["name"])


def test_groups_manage_permission_required(
    app, group_service, user_pub, user_pubres, user_moderator, groups
):
    """Ensure non managers cannot mutate groups."""

    payload = {"name": "perm-check-role"}
    with pytest.raises(PermissionDeniedError):
        group_service.create(user_pub.identity, payload)
    with pytest.raises(PermissionDeniedError):
        group_service.create(user_pubres.identity, {"name": "perm-check-role-2"})

    target = groups[0]
    with pytest.raises(PermissionDeniedError):
        group_service.update(
            user_pub.identity,
            target.name,
            {"description": "attempted change"},
        )

    with pytest.raises(PermissionDeniedError):
        group_service.delete(user_pub.identity, target.name)

    created = group_service.create(
        user_moderator.identity,
        {"name": "perm-check-role-admin", "description": "managed"},
    ).to_dict()
    assert created["id"] == "perm-check-role-admin"

    updated = group_service.update(
        user_moderator.identity,
        "perm-check-role-admin",
        {"description": "updated by admin"},
    ).to_dict()
    assert updated["description"] == "updated by admin"

    assert group_service.delete(user_moderator.identity, "perm-check-role-admin")


def test_groups_recreate_same_name(app, group_service):
    """Recreating a role with the same name should succeed."""

    payload = {"name": "recreate-role", "description": "first"}
    group_service.create(system_identity, payload)
    assert group_service.delete(system_identity, payload["name"])

    recreated = group_service.create(system_identity, payload).to_dict()
    assert recreated["id"] == payload["name"]

    assert group_service.delete(system_identity, payload["name"])
