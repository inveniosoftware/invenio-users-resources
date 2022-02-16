# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Resources for users and roles/groups."""

from .groups import GroupsResource, GroupsResourceConfig
from .users import UsersResource, UsersResourceConfig

__all__ = (
    "GroupsResource",
    "GroupsResourceConfig",
    "UsersResource",
    "UsersResourceConfig",
)
