# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2023-2025 Graz University of Technology.
# Copyright (C) 2024 Ubiquity Press.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User and user group schemas."""

import re

from flask import current_app
from invenio_access.permissions import system_user_id
from invenio_accounts.models import DomainCategory
from invenio_accounts.profiles.schemas import (
    validate_locale,
    validate_timezone,
    validate_visibility,
)
from invenio_accounts.utils import DomainStatus
from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.records.schema import (
    BaseGhostSchema,
    BaseRecordSchema,
)
from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    post_load,
    pre_load,
    validate,
    validates_schema,
)
from marshmallow_utils.context import context_schema
from marshmallow_utils.fields import Links, SanitizedUnicode, TZDateTime
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


def validate_username(value):
    """Validate username against accounts username regular expresion."""
    username_regex = current_app.config["ACCOUNTS_USERNAME_REGEX"]
    if not re.fullmatch(username_regex, value):
        raise ValidationError(str(current_app.config["ACCOUNTS_USERNAME_RULES_TEXT"]))


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

    email = fields.Email(required=True)
    domain = fields.String()
    domaininfo = fields.Nested(DomainInfoSchema)
    identities = fields.Nested(IdentitiesSchema, dump_default={})
    username = fields.String(validate=validate_username)
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
        current_identity = context_schema.get()["identity"]

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
    email = fields.Constant("noreply@inveniosoftware.org", dump_only=True)


class NotificationPreferences(Schema):
    """Schema for notification preferences."""

    enabled = fields.Bool()


class DomainOrgSchema(Schema):
    """Schema for domain orgs."""

    id = fields.Integer(dump_only=True)
    pid = fields.String(validate=validate.Length(min=1, max=255), required=True)
    name = fields.String(validate=validate.Length(min=1, max=255), required=True)
    props = fields.Dict(
        keys=fields.String(required=True),
        values=fields.String(validate=validate.Length(max=255)),
    )
    is_parent = fields.Boolean(dump_only=True, dump_default=False)

    @validates_schema
    def validate_props(self, data, **kwargs):
        """Apply instance specific validation on props."""
        schema = current_app.config["USERS_RESOURCES_DOMAINS_ORG_SCHEMA"]
        props = data.get("props", {})
        if props:
            schema.load(props)


def validate_domain(value):
    """Domain validation."""
    # Basic validation - zenodo has some pretty funky domains so we are not too
    # strict here.
    if len(value) > 255:
        raise ValidationError("Length must be less than 255.")
    value = value.lower().strip()
    if "." not in value:
        raise ValidationError("Not a domain name.")
    prefix, tld = value.rsplit(".", 1)
    if tld == "":
        raise ValidationError("Not a domain name.")


class DomainSchema(Schema):
    """Schema for user groups."""

    id = fields.Str(dump_only=True)
    domain = fields.String(
        validate=validate_domain, required=True, metadata={"create_only": True}
    )
    tld = fields.String(dump_only=True)
    status = fields.Integer(dump_only=True)
    status_name = fields.String(
        validate=validate.OneOf([s.name for s in list(DomainStatus)]),
        load_default=DomainStatus.new.name,
    )
    category = fields.Integer(dump_only=True, metadata={"read_only": True})
    category_name = fields.String(validate=validate.Length(min=1, max=255))
    flagged = fields.Boolean(dump_default=False, metadata={"checked": False})
    flagged_source = fields.Str(validate=validate.Length(max=255), load_default="")
    org = fields.List(
        fields.Nested(DomainOrgSchema), dump_default=None, load_default=None
    )
    num_users = fields.Integer(dump_only=True)
    num_active = fields.Integer(dump_only=True)
    num_inactive = fields.Integer(dump_only=True)
    num_confirmed = fields.Integer(dump_only=True)
    num_verified = fields.Integer(dump_only=True)
    num_blocked = fields.Integer(dump_only=True)
    created = TZDateTime(dump_only=True)
    updated = TZDateTime(dump_only=True)
    links = Links(dump_only=True)

    class Meta:
        """Schema meta."""

        unknown = EXCLUDE

    @pre_load
    def preprocess(self, data, **kwargs):
        """Preprocess form data."""
        # Handle misbehaving clients.
        if "org" in data and data["org"] == "":
            del data["org"]
        return data

    @post_load
    def postprocess(self, data, **kwargs):
        """Process output data."""
        data["domain"] = data["domain"].lower().strip()
        data["domain"].strip()
        data["status_name"] = DomainStatus[data["status_name"]]
        data["status"] = data["status_name"].value
        if "category_name" in data:
            if data["category_name"] is None:
                data["category"] = None
            else:
                category = DomainCategory.get(data["category_name"])
                data["category"] = category.id
        if "org" in data:
            org = data["org"]
            if org is None or len(org) == 0:
                data["org"] = None
            else:
                # discard parent
                data["org"] = org[0]
        return data

    @validates_schema
    def validate_category(self, data, **kwargs):
        """Validate category data."""
        if "category_name" in data and data["category_name"] is not None:
            category = DomainCategory.get(data["category_name"])
            if category is None:
                raise ValidationError("Invalid category_name.")
