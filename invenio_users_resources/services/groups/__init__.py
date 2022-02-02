# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Services for user roles/groups."""

from .config import GroupsServiceConfig
from .service import GroupsService

__all__ = (
    "GroupsService",
    "GroupsServiceConfig",
)
