# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-License-Identifier: MIT

"""Resources for user roles/groups."""

from .config import GroupsResourceConfig
from .resource import GroupsResource

__all__ = (
    "GroupsResource",
    "GroupsResourceConfig",
)
