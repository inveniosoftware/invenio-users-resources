# SPDX-FileCopyrightText: 2025 Northwestern University.
# SPDX-License-Identifier: MIT

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
