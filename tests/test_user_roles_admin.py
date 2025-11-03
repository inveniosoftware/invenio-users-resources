# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Ensure roles are exposed in administration responses."""

from types import SimpleNamespace

import pytest

from invenio_users_resources.records.api import UserAggregate
from invenio_users_resources.services.users.results import UserList

pytestmark = pytest.mark.usefixtures("app", "database")


def _expected_roles(user_fixture):
    """Return the comma separated role names for the given user fixture."""
    roles = sorted(role.name for role in (user_fixture.user.roles or []))
    return ", ".join(roles)


def test_read_includes_roles(user_service, user_moderator):
    """Roles appear in admin detail responses."""
    result = user_service.read(
        user_moderator.identity,
        user_moderator.user.id,
    ).to_dict()

    expected = _expected_roles(user_moderator)
    assert result["roles"] == expected
    assert result["roles_label"] == expected
    assert result["profile"]["roles"] == expected


def test_read_without_roles_returns_empty_string(
    user_service, user_moderator, user_pub
):
    """Users without roles expose an empty roles string."""
    result = user_service.read(
        user_moderator.identity,
        user_pub.user.id,
    ).to_dict()

    assert result["roles"] == ""
    assert result["roles_label"] == ""
    assert result["profile"]["roles"] == ""


def test_user_list_populates_roles(user_service, user_moderator, user_pub):
    """UserList projection populates role information."""
    moderator_doc = UserAggregate.from_model(user_moderator.user).dumps()
    user_doc = UserAggregate.from_model(user_pub.user).dumps()

    results = [
        SimpleNamespace(to_dict=lambda doc=moderator_doc: doc),
        SimpleNamespace(to_dict=lambda doc=user_doc: doc),
    ]

    user_list = UserList(
        service=user_service,
        identity=user_moderator.identity,
        results=results,
        params=None,
        links_tpl=None,
        links_item_tpl=None,
    )

    hits = list(user_list.hits)

    expected = _expected_roles(user_moderator)
    assert hits[0]["roles"] == expected
    assert hits[0]["roles_label"] == expected
    assert hits[0]["profile"]["roles"] == expected

    assert hits[1]["roles"] == ""
    assert hits[1]["roles_label"] == ""
    assert hits[1]["profile"]["roles"] == ""
