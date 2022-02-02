# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Resources for user roles/groups."""

from .config import GroupsResourceConfig
from .resource import GroupsResource

__all__ = (
    "GroupsResource",
    "GroupsResourceConfig",
)
