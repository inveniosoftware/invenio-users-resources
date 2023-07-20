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
    AnyUser,
    AuthenticatedUser,
    SystemProcess,
)

from .generators import IfPublicEmail, IfPublicUser, Self, UserModeration


class UsersPermissionPolicy(BasePermissionPolicy):
    """Permission policy for users and user groups."""

    can_create = [SystemProcess()]
    can_read = [UserModeration(), IfPublicUser([AnyUser()], [Self()]), SystemProcess()]
    can_search = [UserModeration(), AuthenticatedUser(), SystemProcess()]
    can_update = [SystemProcess()]
    can_delete = [SystemProcess()]

    can_read_email = [IfPublicEmail([AnyUser()], [Self()]), SystemProcess()]
    can_read_details = [Self(), SystemProcess()]

    # Moderation permissions
    can_block = [UserModeration(), SystemProcess()]
    can_approve = [UserModeration(), SystemProcess()]
    can_suspend = [UserModeration(), SystemProcess()]
    can_search_all = [UserModeration(), SystemProcess()]
    can_read_moderation_details = [UserModeration(), SystemProcess()]


class GroupsPermissionPolicy(BasePermissionPolicy):
    """Permission policy for users and user groups."""

    can_create = [SystemProcess()]
    can_read = [AuthenticatedUser(), SystemProcess()]
    can_search = [AuthenticatedUser(), SystemProcess()]
    can_update = [SystemProcess()]
    can_delete = [SystemProcess()]
