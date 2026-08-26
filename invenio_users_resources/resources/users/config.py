# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-FileCopyrightText: 2022 CERN.
# SPDX-FileCopyrightText: 2026 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT

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
from invenio_records_resources.services.errors import PermissionDeniedError
from marshmallow import fields


class UsersSearchRequestArgsSchema(SearchRequestArgsSchema):
    """Add parameter to parse tags."""

    is_active = fields.Boolean()
    is_blocked = fields.Boolean()
    is_verified = fields.Boolean()


class UserGroupsActionSchema(ma.Schema):
    """Schema for bulk user group assignment actions."""

    groups = fields.List(fields.Str(), required=True)


def handle_user_permission_error(err):
    """Handle permission errors without logging exception traceback."""
    response = HTTPJSONException(code=403, description=err.description)
    return response.get_response()


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
        "item": "/<user_id:id>",
        "groups-list": "/<user_id:id>/groups",
        "item-avatar": "/<user_id:id>/avatar.svg",
        "approve": "/<user_id:id>/approve",
        "block": "/<user_id:id>/block",
        "restore": "/<user_id:id>/restore",
        "activate": "/<user_id:id>/activate",
        "deactivate": "/<user_id:id>/deactivate",
        "impersonate": "/<user_id:id>/impersonate",
    }

    request_view_args = {
        "id": ma.fields.Str(),
    }

    request_search_args = UsersSearchRequestArgsSchema

    error_handlers = {
        **ErrorHandlersMixin.error_handlers,
        PermissionDeniedError: handle_user_permission_error,
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
