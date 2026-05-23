# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-FileCopyrightText: 2025 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT

"""Ensure roles are exposed in administration responses."""

import pytest

from invenio_users_resources.records.api import UserAggregate
from invenio_users_resources.services.users.results import (
    _apply_roles,
    _can_manage_groups,
    _role_names,
)

pytestmark = pytest.mark.usefixtures("app", "database")


def _expected_roles(user_fixture):
    """Return the sorted list of role names for the given user fixture."""
    roles = sorted(role.name for role in (user_fixture.user.roles or []))
    return ", ".join(roles)


def test_read_includes_roles(user_service, user_moderator):
    """Roles appear in admin detail responses."""
    result = user_service.read(
        user_moderator.identity,
        user_moderator.user.id,
    ).to_dict()

    expected = _expected_roles(user_moderator)
    assert expected == result["roles"]
    assert expected == result["profile"]["roles"]


def test_read_without_roles_returns_empty_string(
    user_service, user_moderator, user_pub
):
    """Users without roles expose an empty roles string."""
    result = user_service.read(
        user_moderator.identity,
        user_pub.user.id,
    ).to_dict()

    assert not result["roles"]
    assert not result["profile"]["roles"]


def test_user_list_populates_roles(user_service, user_moderator, user_pub):
    """UserList projection populates role information."""
    moderator_aggregate = UserAggregate.from_model(user_moderator.user)
    roles = _role_names(moderator_aggregate)
    has_permission = _can_manage_groups(user_moderator.identity, user_service)
    # user with roles
    payload = {}
    _apply_roles(payload, roles, has_permission)
    expected = _expected_roles(user_moderator)
    assert expected == payload["roles"]
    assert expected == payload["profile"]["roles"]
    # user without roles
    user_aggregate = UserAggregate.from_model(user_pub.user)
    roles_pub = _role_names(user_aggregate)
    payload_pub = {}
    _apply_roles(payload_pub, roles_pub, has_permission)
    assert not payload_pub["roles"]
    assert not payload_pub["profile"]["roles"]
