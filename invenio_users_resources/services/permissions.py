# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users and user groups permissions."""

from invenio_records_permissions import BasePermissionPolicy
from invenio_records_permissions.generators import (
    AdminAction,
    AnyUser,
    AuthenticatedUser,
    SystemProcess,
)

from invenio_users_resources.permissions import user_management_action

from .generators import IfGroupNotManaged, IfPublicEmail, IfPublicUser, Self

UserManager = AdminAction(user_management_action)


class UsersPermissionPolicy(BasePermissionPolicy):
    """Permission policy for users and user groups."""

    can_create = [SystemProcess()]
    can_read = [
        UserManager,
        IfPublicUser(then_=[AnyUser()], else_=[Self()]),
        SystemProcess(),
    ]
    can_search = [AuthenticatedUser(), SystemProcess()]
    can_update = [SystemProcess()]
    can_delete = [SystemProcess()]

    can_read_email = [
        UserManager,
        IfPublicEmail([AnyUser()], [Self()]),
        SystemProcess(),
    ]
    can_read_details = [UserManager, Self(), SystemProcess()]

    # Moderation permissions
    can_manage = [UserManager, SystemProcess()]
    can_search_all = [UserManager, SystemProcess()]
    can_read_system_details = [UserManager, SystemProcess()]
    can_impersonate = [UserManager, SystemProcess()]


class GroupsPermissionPolicy(BasePermissionPolicy):
    """Permission policy for users and user groups."""

    can_create = [SystemProcess()]
    can_read = [
        IfGroupNotManaged([AuthenticatedUser()], [UserManager]),
        SystemProcess(),
    ]
    can_search = [AuthenticatedUser(), SystemProcess()]
    can_update = [SystemProcess()]
    can_delete = [SystemProcess()]


class DomainPermissionPolicy(BasePermissionPolicy):
    """Permission policy for users and user groups."""

    can_create = [UserManager, SystemProcess()]
    can_read = [UserManager, SystemProcess()]
    can_search = [UserManager, SystemProcess()]
    can_update = [UserManager, SystemProcess()]
    can_delete = [UserManager, SystemProcess()]
