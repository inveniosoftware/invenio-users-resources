# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User and user group schemas."""

from invenio_access.permissions import system_user_id
from invenio_accounts.profiles.schemas import (
    validate_locale,
    validate_timezone,
    validate_visibility,
)
from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.records.schema import (
    BaseGhostSchema,
    BaseRecordSchema,
)
from marshmallow import Schema, fields
from marshmallow_utils.fields import SanitizedUnicode, TZDateTime
from marshmallow_utils.permissions import FieldPermissionsMixin


class DomainInfoSchema(Schema):
    """Schema for domain info."""

    status = fields.String()
    tld = fields.String()
    flagged = fields.Boolean()


class IdentitiesSchema(Schema):
    """Schema for domain info."""

    github = fields.String()
    orcid = fields.String()


class UserPreferencesSchema(Schema):
    """Schema for user preferences."""

    visibility = fields.String(validate=validate_visibility)
    email_visibility = fields.String(validate=validate_visibility)
    locale = fields.String(validate=validate_locale)
    timezone = fields.String(validate=validate_timezone)


class UserProfileSchema(Schema):
    """Schema for user profiles."""

    full_name = fields.String()
    affiliations = fields.String()


class UserSchema(BaseRecordSchema, FieldPermissionsMixin):
    """Schema for users."""

    field_dump_permissions = {
        "email": "read_email",
        "domain": "read_details",
        "created": "read_details",
        "updated": "read_details",
        "revision_id": "read_details",
        "active": "read_details",
        "status": "read_system_details",
        "visibility": "read_system_details",
        "confirmed": "read_details",
        "verified": "read_details",
        "blocked": "read_details",
        "preferences": "read_details",
        "domaininfo": "read_system_details",
        "blocked_at": "read_system_details",
        "verified_at": "read_system_details",
        "confirmed_at": "read_system_details",
        "current_login_at": "read_system_details",
    }

    # NOTE: API should only deliver users that are active & confirmed
    active = fields.Boolean()
    confirmed = fields.Boolean(dump_only=True)
    blocked = fields.Boolean(dump_only=True)
    verified = fields.Boolean(dump_only=True)
    status = fields.Str(dump_only=True)
    visibility = fields.Str(dump_only=True)
    is_current_user = fields.Method("is_self", dump_only=True)

    email = fields.String()
    domain = fields.String()
    domaininfo = fields.Nested(DomainInfoSchema)
    identities = fields.Nested(IdentitiesSchema, default={})
    username = fields.String()
    profile = fields.Dict()
    preferences = fields.Nested(UserPreferencesSchema)

    blocked_at = TZDateTime(dump_only=True)
    verified_at = TZDateTime(dump_only=True)
    confirmed_at = TZDateTime(dump_only=True)
    current_login_at = TZDateTime(dump_only=True)
    created = TZDateTime(dump_only=True)
    updated = TZDateTime(dump_only=True)

    def is_self(self, obj):
        """Determine if identity is the current identity."""
        current_identity = self.context["identity"]

        _id = obj.get("id") or obj.id

        return (
            _id is not None
            and current_identity.id is not None
            and str(_id) == str(current_identity.id)
        )


class GroupSchema(BaseRecordSchema):
    """Schema for user groups."""

    name = fields.String()
    title = fields.String()
    description = fields.String()
    provider = fields.String(dump_only=True)
    is_managed = fields.Boolean(dump_only=True)


class UserGhostSchema(BaseGhostSchema):
    """User ghost schema."""

    id = SanitizedUnicode(dump_only=True)
    profile = fields.Constant(
        {
            "full_name": _("Deleted user"),
        },
        dump_only=True,
    )
    username = fields.Constant(_("Deleted user"), dump_only=True)


class SystemUserSchema(BaseGhostSchema):
    """System user schema."""

    id = fields.Constant(system_user_id, dump_only=True)
    profile = fields.Constant(
        {
            "full_name": _("System"),
        },
        dump_only=True,
    )
    username = fields.Constant(_("System"), dump_only=True)


class NotificationPreferences(Schema):
    """Schema for notification preferences."""

    enabled = fields.Bool()
