# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users resource config."""

import marshmallow as ma
from invenio_records_resources.resources import (
    RecordResourceConfig,
    SearchRequestArgsSchema,
)
from marshmallow import fields


class UsersSearchRequestArgsSchema(SearchRequestArgsSchema):
    """Add parameter to parse tags."""

    is_active = fields.Boolean()
    is_blocked = fields.Boolean()
    is_verified = fields.Boolean()


#
# Resource config
#
class UsersResourceConfig(RecordResourceConfig):
    """Users resource configuration."""

    blueprint_name = "users"
    url_prefix = "/users"
    routes = {
        "list": "",
        "moderation_search": "/moderation",
        "item": "/<id>",
        "item-avatar": "/<id>/avatar.svg",
        "approve": "/<id>/approve",
        "block": "/<id>/block",
        "restore": "/<id>/restore",
        "deactivate": "/<id>/deactivate",
    }

    request_view_args = {
        "id": ma.fields.Str(),
    }

    request_search_args = UsersSearchRequestArgsSchema
