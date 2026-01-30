# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2024 KTH Royal Institute of Technology.
# Copyright (C) 2024 Ubiquity Press.
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users and user groups permissions."""

from invenio_access import superuser_access
from invenio_records_permissions import BasePermissionPolicy
from invenio_records_permissions.generators import (
    AdminAction,
    AnyUser,
    AuthenticatedUser,
    SystemProcess,
)

from invenio_users_resources.permissions import user_management_action

from .generators import (
    AdministrationGroupAction,
    AdministrationUserAction,
    DenyAll,
    GroupsEnabled,
    IfGroupNotManaged,
    IfPublicEmail,
    IfPublicUser,
    IfSuperAdmin,
    PreventSelf,
    ProtectedGroupIdentifiers,
    Self,
)

UserManager = AdministrationUserAction(user_management_action)
GroupManager = AdministrationGroupAction(user_management_action)
SuperAdmin = AdminAction(superuser_access)


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
    can_read_all = [UserManager, SystemProcess()]

    # Moderation permissions
    can_manage = [UserManager, PreventSelf(), SystemProcess()]
    can_search_all = [UserManager, SystemProcess()]
    can_read_system_details = [UserManager, SystemProcess()]
    can_impersonate = [
        IfSuperAdmin(
            then_=[SuperAdmin],
            else_=[UserManager],
        ),
        PreventSelf(),
        SystemProcess(),
    ]
    can_manage_groups = [
        IfSuperAdmin(
            then_=[SuperAdmin],
            else_=[GroupManager],
        ),
        SystemProcess(),
    ]


class GroupsPermissionPolicy(BasePermissionPolicy):
    """Permission policy for users and user groups."""

    _can_any = [
        GroupsEnabled("group"),
        SystemProcess(),
    ]
    can_read = _can_any + [
        IfSuperAdmin(
            then_=[SuperAdmin],
            else_=[
                IfGroupNotManaged([AuthenticatedUser()], [GroupManager]),
            ],
        ),
    ]
    can_search = _can_any + [AuthenticatedUser()]
    can_create = [ProtectedGroupIdentifiers(), GroupManager, SystemProcess()]
    can_update = _can_any + [
        ProtectedGroupIdentifiers(),
        IfSuperAdmin(
            then_=[SuperAdmin],
            else_=[
                IfGroupNotManaged([DenyAll()], [GroupManager]),
            ],
        ),
    ]
    can_delete = _can_any + [
        ProtectedGroupIdentifiers(),
        IfSuperAdmin(
            then_=[SuperAdmin],
            else_=[
                IfGroupNotManaged([DenyAll()], [GroupManager]),
            ],
        ),
        SystemProcess(),
    ]


class DomainPermissionPolicy(BasePermissionPolicy):
    """Permission policy for users and user groups."""

    can_create = [UserManager, SystemProcess()]
    can_read = [UserManager, SystemProcess()]
    can_search = [UserManager, SystemProcess()]
    can_update = [UserManager, SystemProcess()]
    can_delete = [UserManager, SystemProcess()]
