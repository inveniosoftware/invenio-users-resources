# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# invenio-administration is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio administration users view module."""
from invenio_administration.views.base import (
    AdminResourceCreateView,
    AdminResourceDetailView,
    AdminResourceEditView,
    AdminResourceListView,
)
from invenio_i18n import lazy_gettext as _


class UsersListView(AdminResourceListView):
    """Configuration for users sets list view."""

    api_endpoint = "/users/sets"
    name = "USERS"
    resource_config = "users_resource"
    search_request_headers = {"Accept": "application/json"}
    title = "USERS Sets"
    category = "User management"
    pid_path = "id"
    icon = "exchange"
    template = "invenio_users_resources/users-search.html"

    display_search = True
    display_delete = True
    display_edit = True

    item_field_list = {
        "spec": {"text": _("Set spec"), "order": 1},
        "name": {"text": _("Set name"), "order": 2},
        "search_pattern": {"text": _("Search query"), "order": 3},
        "created": {"text": _("Created"), "order": 4},
        "updated": {"text": _("Updated"), "order": 5},
    }

    search_config_name = "RDM_users_SEARCH"
    search_facets_config_name = "RDM_users_FACETS"
    search_sort_config_name = "RDM_users_SORT_OPTIONS"

    create_view_name = "users_create"
    resource_name = "name"


class UsersEditView(AdminResourceEditView):
    """Configuration for users sets edit view."""

    name = "users_edit"
    url = "/users/<pid_value>/edit"
    resource_config = "users_resource"
    pid_path = "id"
    api_endpoint = "/users/sets"
    title = "Edit USERS set"

    list_view_name = "USERS"

    form_fields = {
        "name": {
            "order": 1,
            "text": _("Set name"),
            "description": _("A short human-readable string naming the set."),
        },
        "spec": {
            "order": 2,
            "text": _("Set spec"),
            "description": _(
                "An identifier for the set, "
                "which cannot be edited after the set is created."
            ),
        },
        "search_pattern": {
            "order": 3,
            "text": _("Search query"),
            "description": _(
                "See the supported query "
                "syntax in the "
                "<a href='/help/search'>Search Guide</a>."
            ),
        },
        "created": {"order": 4},
        "updated": {"order": 5},
    }


class UsersCreateView(AdminResourceCreateView):
    """Configuration for users sets create view."""

    name = "users_create"
    url = "/users/create"
    resource_config = "users_resource"
    pid_path = "id"
    api_endpoint = "/users/sets"
    title = "Create USERS set"

    list_view_name = "USERS"

    form_fields = {
        "name": {
            "order": 1,
            "text": _("Set name"),
            "description": _("A short human-readable string naming the set."),
        },
        "spec": {
            "order": 2,
            "text": _("Set spec"),
            "description": _(
                "An identifier for the set, "
                "which cannot be edited after the set is created."
            ),
        },
        "search_pattern": {
            "order": 3,
            "text": _("Search query"),
            "description": _(
                "See the supported query "
                "syntax in the <a href='/help/search'>Search Guide</a>."
            ),
        },
    }


class UsersDetailView(AdminResourceDetailView):
    """Configuration for users sets detail view."""

    url = "/users/<pid_value>"
    api_endpoint = "/users/sets"
    search_request_headers = {"Accept": "application/json"}
    name = "USERS details"
    resource_config = "users_resource"
    title = "USERS Details"

    template = "invenio_users_resources/users-details.html"
    display_delete = True
    display_edit = True

    list_view_name = "USERS"
    pid_path = "id"

    item_field_list = {
        "name": {"text": _("Set name"), "order": 1},
        "spec": {"text": _("Set spec"), "order": 2},
        "search_pattern": {"text": _("Search query"), "order": 3},
        "created": {"text": _("Created"), "order": 4},
        "updated": {"text": _("Updated"), "order": 5},
    }
