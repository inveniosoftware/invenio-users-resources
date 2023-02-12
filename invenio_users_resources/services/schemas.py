# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User and user group schemas."""

from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.records.schema import BaseRecordSchema
from marshmallow import Schema, ValidationError, fields
from marshmallow_utils.permissions import FieldPermissionsMixin


def validate_visibility(value):
    """Check if the value is a valid visibility setting."""
    if value not in ["public", "restricted"]:
        raise ValidationError(
            message=str(_("Value must be either 'public' or 'restricted'."))
        )


class UserPreferencesSchema(Schema):
    """Schema for user preferences."""

    visibility = fields.String(validate=validate_visibility)
    email_visibility = fields.String(validate=validate_visibility)


class UserProfileSchema(Schema):
    """Schema for user profiles."""

    full_name = fields.String()
    affiliations = fields.String()


class UserSchema(BaseRecordSchema, FieldPermissionsMixin):
    """Schema for users."""

    field_dump_permissions = {
        "email": "read_email",
        "created": "read_details",
        "updated": "read_details",
        "revision_id": "read_details",
        "active": "read_details",
        "confirmed": "read_details",
        "preferences": "read_details",
    }

    # NOTE: API should only deliver users that are active & confirmed
    active = fields.Boolean()
    confirmed = fields.Boolean(dump_only=True)
    is_current_user = fields.Method("is_self", dump_only=True)

    email = fields.String()
    username = fields.String()
    profile = fields.Dict()
    preferences = fields.Nested(UserPreferencesSchema)

    def is_self(self, obj):
        """Determine if identity is the current identity."""
        current_identity = self.context["identity"]
        return (
            obj.id is not None
            and current_identity.id is not None
            and str(obj.id) == str(current_identity.id)
        )


class GroupSchema(BaseRecordSchema):
    """Schema for user groups."""

    name = fields.String()
    title = fields.String()
    description = fields.String()
    provider = fields.String(dump_only=True)
    is_managed = fields.Boolean(dump_only=True)
