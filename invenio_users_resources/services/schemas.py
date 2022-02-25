# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User and user group schemas."""

from flask_babelex import lazy_gettext as _
from invenio_records_resources.services.records.schema import BaseRecordSchema
from marshmallow import Schema, ValidationError, fields
from marshmallow_utils.permissions import FieldPermissionsMixin


def validate_visibility(value):
    """Check if the value is a valid visibility setting."""
    if value not in ["public", "restricted"]:
        raise ValidationError(
            message=str(_("Value must be either 'public' or 'restricted'."))
        )


class UserAccessSchema(Schema):
    """Schema for user access."""

    visibility = fields.String(validate=validate_visibility)
    email_visibility = fields.String(validate=validate_visibility)


class UserProfileSchema(Schema):
    """Schema for user profiles."""

    username = fields.String()
    full_name = fields.String()
    # TODO fields: affiliations, bio, location, url, ...
    #      will they be customizable?


class UserSchema(BaseRecordSchema, FieldPermissionsMixin):
    """Schema for users."""

    field_dump_permissions = {
        "email": "read_email",
        "created": "read_details",
        "updated": "read_details",
        "revision_id": "read_details",
        "active": "read_details",
        "confirmed": "read_details",
        "identities": "read_details",
        "preferences": "read_details",
    }

    # NOTE: API should only deliver users that are active & confirmed
    active = fields.Boolean()
    confirmed = fields.Boolean(dump_only=True)
    is_current_user = fields.Boolean(dump_only=True)

    email = fields.String()
    profile = fields.Dict()
    identities = fields.Dict()  # TODO how to find out the contents?
    preferences = fields.Dict()  # TODO the content will be customizable?
    access = fields.Nested(UserAccessSchema)


class GroupSchema(BaseRecordSchema):
    """Schema for user groups."""

    name = fields.String()
    title = fields.String()
    description = fields.String()
    provider = fields.String(dump_only=True)
    is_managed = fields.Boolean(dump_only=True)
