# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2024 KTH Royal Institute of Technology.
# Copyright (C) 2024 Ubiquity Press.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users and user groups permissions."""

from invenio_records_permissions import BasePermissionPolicy
from invenio_records_permissions.generators import (
    AdminAction,
    AuthenticatedUser,
    SystemProcess,
)

from invenio_users_resources.permissions import user_management_action

from .generators import (
    GroupsEnabled,
    IfGroupNotManaged,
    IfPublicEmail,
    IfPublicUser,
    PreventSelf,
    Self,
)

UserManager = AdminAction(user_management_action)


class UsersPermissionPolicy(BasePermissionPolicy):
    """Permission policy for users and user groups."""

    can_create = [UserManager, SystemProcess()]
    can_read = [
        UserManager,
        IfPublicUser(then_=[AuthenticatedUser()], else_=[Self()]),
        SystemProcess(),
    ]
    can_search = [AuthenticatedUser(), SystemProcess()]
    can_update = [SystemProcess()]
    can_delete = [SystemProcess()]

    can_read_email = [
        UserManager,
        IfPublicEmail([AuthenticatedUser()], [Self()]),
        SystemProcess(),
    ]
    can_read_details = [UserManager, Self(), SystemProcess()]
    can_read_all = [UserManager, SystemProcess()]

    # Moderation permissions
    can_manage = [UserManager, PreventSelf(), SystemProcess()]
    can_search_all = [UserManager, SystemProcess()]
    can_read_system_details = [UserManager, SystemProcess()]
    can_impersonate = [UserManager, PreventSelf(), SystemProcess()]


class GroupsPermissionPolicy(BasePermissionPolicy):
    """Permission policy for users and user groups."""

    _can_any = [
        GroupsEnabled("group"),
        SystemProcess(),
    ]
    can_create = _can_any
    can_read = _can_any + [
        IfGroupNotManaged([AuthenticatedUser()], [UserManager]),
    ]
    can_search = _can_any + [AuthenticatedUser()]
    can_update = _can_any
    can_delete = _can_any


class DomainPermissionPolicy(BasePermissionPolicy):
    """Permission policy for users and user groups."""

    can_create = [UserManager, SystemProcess()]
    can_read = [UserManager, SystemProcess()]
    can_search = [UserManager, SystemProcess()]
    can_update = [UserManager, SystemProcess()]
    can_delete = [UserManager, SystemProcess()]
