# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Ubiquity Press.
# Copyright (C) 2026 KTH Royal Institute of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permission generators tests."""

from invenio_access.utils import get_identity
from invenio_records_permissions.generators import AuthenticatedUser

from invenio_users_resources.permissions import user_management_action
from invenio_users_resources.services.generators import IfGroupNotManaged, PreventSelf
from invenio_users_resources.services.permissions import UserManager


def test_group_not_managed_generator(app, user_pub, user_moderator):
    """Test IfGroupNotManaged generator."""

    permission = IfGroupNotManaged([AuthenticatedUser()], [UserManager])

    assert permission.needs() == {user_management_action}
    assert permission.needs(record={"is_managed": True}) == {user_management_action}

    identity = get_identity(user_pub)
    query = permission.query_filter(identity=identity)
    assert query.to_dict() == {"match": {"is_managed": False}}

    identity = get_identity(user_moderator)
    query = permission.query_filter(identity=identity)
    assert query.to_dict() == {"match_all": {}}


def test_prevent_self_compares_ids_type_insensitively(user_pub):
    """PreventSelf should block self-actions for str/int id mismatches."""
    permission = PreventSelf()
    excludes = permission.excludes(record=user_pub, actor_id=str(user_pub.id))
    assert len(excludes) == 1
