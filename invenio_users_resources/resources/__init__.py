# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-License-Identifier: MIT

"""Resources for users and roles/groups."""

from .domains import DomainsResource, DomainsResourceConfig
from .groups import GroupsResource, GroupsResourceConfig
from .users import UsersResource, UsersResourceConfig

__all__ = (
    "DomainsResource",
    "DomainsResourceConfig",
    "GroupsResource",
    "GroupsResourceConfig",
    "UsersResource",
    "UsersResourceConfig",
)
