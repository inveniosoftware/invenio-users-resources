# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""User and user group schemas."""

from flask_babelex import lazy_gettext as _
from invenio_records_resources.services.records.schema import BaseRecordSchema
from marshmallow import Schema, ValidationError, fields


def validate_visibility(value):
    """Check if the value is a valid visibility setting."""
    if value not in ["public", "restricted"]:
        raise ValidationError(
            _("Value must be either 'public' or 'restricted'.")
        )


class UserAccessSchema(Schema):
    """Schema for user access."""

    visibility = fields.String(validate=validate_visibility)
    email_visibility = fields.String(validate=validate_visibility)


class UserSchema(BaseRecordSchema):
    """Schema for users."""

    # NOTE: API should only deliver users that are active & confirmed
    active = fields.Boolean()
    confirmed = fields.Boolean(dump_only=True)

    email = fields.String()
    username = fields.String()
    full_name = fields.String()

    profile = fields.Dict()  # TODO the contents will be customizable?
    identities = fields.Dict()  # TODO how to find out the contents?
    preferences = fields.Dict()  # TODO the content will be customizable?
    access = fields.Nested(UserAccessSchema)


class GroupSchema(BaseRecordSchema):
    """Schema for user groups."""

    name = fields.String()
    description = fields.String()
