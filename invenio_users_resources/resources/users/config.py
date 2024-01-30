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
from flask_resources import HTTPJSONException, create_error_handler
from invenio_cache.errors import LockAcquireFailed
from invenio_i18n import lazy_gettext as _
from invenio_records_resources.resources import (
    RecordResourceConfig,
    SearchRequestArgsSchema,
)
from invenio_records_resources.resources.errors import ErrorHandlersMixin
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
        "search_all": "/all",
        "item": "/<id>",
        "item-avatar": "/<id>/avatar.svg",
        "approve": "/<id>/approve",
        "block": "/<id>/block",
        "restore": "/<id>/restore",
        "activate": "/<id>/activate",
        "deactivate": "/<id>/deactivate",
        "impersonate": "/<id>/impersonate",
    }

    request_view_args = {
        "id": ma.fields.Str(),
    }

    request_search_args = UsersSearchRequestArgsSchema

    error_handlers = {
        **ErrorHandlersMixin.error_handlers,
        LockAcquireFailed: create_error_handler(
            lambda e: (
                HTTPJSONException(
                    code=400,
                    description=_(
                        "User is locked due to concurrent running operation."
                    ),
                )
            )
        ),
    }

    response_handlers = {
        "application/vnd.inveniordm.v1+json": RecordResourceConfig.response_handlers[
            "application/json"
        ],
        **RecordResourceConfig.response_handlers,
    }
