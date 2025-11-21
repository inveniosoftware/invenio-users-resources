# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test administration views for users."""

from invenio_administration.views.base import (
    AdminResourceListView,
)


class UsersListView(AdminResourceListView):
    """Configuration for users sets list view."""

    name = "users"
    resource_config = "users_resource"


class UserModerationListView(AdminResourceListView):
    """User moderation admin search view."""

    name = "moderation"
    resource_config = "requests_resource"
