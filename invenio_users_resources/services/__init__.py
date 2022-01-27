# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Services for users and user roles/groups."""

from .groups import UserGroupsService, UserGroupsServiceConfig
from .users import UsersService, UsersServiceConfig

__all__ = (
    "UsersService",
    "UsersServiceConfig",
    "UserGroupsService",
    "UserGroupsServiceConfig",
)
