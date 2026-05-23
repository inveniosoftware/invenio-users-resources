# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-License-Identifier: MIT

"""Data-layer definitions for user and group management in Invenio."""

from .api import GroupAggregate, UserAggregate

__all__ = (
    "UserAggregate",
    "GroupAggregate",
)
