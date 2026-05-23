# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-License-Identifier: MIT

"""Resources for user roles/groups."""

from .config import DomainsResourceConfig
from .resource import DomainsResource

__all__ = (
    "DomainsResource",
    "DomainsResourceConfig",
)
