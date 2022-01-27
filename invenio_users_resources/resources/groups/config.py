# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User roles/groups resource config."""


import marshmallow as ma
from invenio_records_resources.resources import RecordResourceConfig, \
    SearchRequestArgsSchema


#
# Request args
#
class UserGroupSearchRequestArgsSchema(SearchRequestArgsSchema):
    """Add parameter to parse tags."""

    title = ma.fields.String()


#
# Resource config
#
class UserGroupsResourceConfig(RecordResourceConfig):
    """User groups resource configuration."""

    blueprint_name = "groups"
    url_prefix = "/groups"
    routes = {
        "list": "",
        "item": "/<id>",
        "avatar": "/<id>/avatar.svg",
    }

    request_view_args = {
        "id": ma.fields.Str(),
    }

    request_search_args = UserGroupSearchRequestArgsSchema
