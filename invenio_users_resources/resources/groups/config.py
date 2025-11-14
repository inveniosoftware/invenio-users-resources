# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User roles/groups resource config."""

import marshmallow as ma
from flask_resources import HTTPJSONException
from invenio_records_resources.errors import validation_error_to_list_errors
from invenio_records_resources.resources import (
    RecordResource,
    RecordResourceConfig,
    SearchRequestArgsSchema,
)
from invenio_records_resources.resources.errors import PermissionDeniedError
from marshmallow import ValidationError

from .errors import GroupValidationError


#
# Request args
#
class GroupSearchRequestArgsSchema(SearchRequestArgsSchema):
    """Add parameter to parse tags."""

    title = ma.fields.String()


def handle_group_validation_error(err):
    """Handle groups errors."""
    marshmallow_error = ValidationError(err.errors or {})
    response = HTTPJSONException(
        code=400,
        description=err.description,
        errors=validation_error_to_list_errors(marshmallow_error),
    )
    return response.get_response()


def handle_group_permission_error(err):
    """Handle permission errors."""
    response = HTTPJSONException(code=403, description=err.description)
    return response.get_response()


#
# Resource config
#
class GroupsResourceConfig(RecordResourceConfig):
    """User groups resource configuration."""

    blueprint_name = "groups"
    url_prefix = "/groups"
    routes = {
        "list": "",
        "item": "/<id>",
        "item-avatar": "/<id>/avatar.svg",
    }

    request_view_args = {
        "id": ma.fields.Str(),
    }

    request_search_args = GroupSearchRequestArgsSchema

    error_handlers = {
        **RecordResource.error_handlers,
        GroupValidationError: handle_group_validation_error,
        PermissionDeniedError: handle_group_permission_error,
    }

    response_handlers = {
        "application/vnd.inveniordm.v1+json": RecordResourceConfig.response_handlers[
            "application/json"
        ],
        **RecordResourceConfig.response_handlers,
    }
