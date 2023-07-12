# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# invenio-administration is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio administration users view module."""
from flask import current_app
from invenio_administration.views.base import (
    AdminResourceDetailView,
    AdminResourceListView,
)
from invenio_i18n import lazy_gettext as _

USERS_ITEM_LIST = {
    "username": {"text": _("Username"), "order": 1},
    "email": {"text": _("Email"), "order": 2},
    "created": {"text": _("Created"), "order": 3},
    "updated": {"text": _("Updated"), "order": 4},
    "active": {"text": _("Active"), "order": 5},
    "confirmed": {"text": _("Confirmed"), "order": 6},
}
# List of the columns displayed on the user list and user details


class UsersListView(AdminResourceListView):
    """Configuration for users sets list view."""

    api_endpoint = "/users"
    name = "users"
    resource_config = "users_resource"
    title = "User management"
    menu_label = "Users"
    category = "User management"
    pid_path = "id"
    icon = "users"

    display_search = True
    display_delete = False
    display_edit = False
    display_create = False

    item_field_list = USERS_ITEM_LIST

    search_config_name = "USERS_RESOURCES_SEARCH"
    search_sort_config_name = "USERS_RESOURCES_SORT_OPTIONS"

    @staticmethod
    def disabled():
        """Disable the view on demand."""
        return not current_app.config["USERS_RESOURCES_ADMINISTRATION_ENABLED"]


class UsersDetailView(AdminResourceDetailView):
    """Configuration for users sets detail view."""

    url = "/users/<pid_value>"
    api_endpoint = "/users/"
    search_request_headers = {"Accept": "application/json"}
    name = "User details"
    resource_config = "users_resource"
    title = "User Details"
    display_delete = False
    display_edit = False

    pid_path = "username"
    item_field_list = USERS_ITEM_LIST
