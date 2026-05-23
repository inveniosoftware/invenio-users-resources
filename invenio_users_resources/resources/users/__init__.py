# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-License-Identifier: MIT

"""Resources for users."""

from .config import UsersResourceConfig
from .resource import UsersResource

__all__ = (
    "UsersResource",
    "UsersResourceConfig",
)
