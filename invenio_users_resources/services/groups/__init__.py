# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-License-Identifier: MIT

"""Services for user roles/groups."""

from .config import GroupsServiceConfig
from .service import GroupsService

__all__ = (
    "GroupsService",
    "GroupsServiceConfig",
)
