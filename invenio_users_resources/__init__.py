# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio module providing management APIs for users and roles/groups."""

from .ext import InvenioUsersResources
from .proxies import current_groups_service, current_user_resources, \
    current_users_service
from .version import __version__

__all__ = (
    "__version__",
    "current_user_resources",
    "current_users_service",
    "current_groups_service",
    "InvenioUsersResources",
)
