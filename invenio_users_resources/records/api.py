# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
# Copyright (C) 2024 Graz University of Technology.
# Copyright (C) 2024 Ubiquity Press.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""API classes for user and group management in Invenio."""

import unicodedata
from collections import namedtuple
from datetime import datetime

from flask import current_app
from invenio_accounts.models import Domain, User
from invenio_accounts.proxies import current_datastore
from invenio_db import db
from invenio_i18n import lazy_gettext as _
from invenio_records.dumpers import SearchDumper, SearchDumperExt
from invenio_records.dumpers.indexedat import IndexedAtDumperExt
from invenio_records.systemfields import ModelField
from invenio_records_resources.records.api import Record
from invenio_records_resources.records.systemfields import IndexField
from marshmallow import ValidationError
from sqlalchemy.exc import NoResultFound

from .dumpers import EmailFieldDumperExt
from .models import DomainAggregateModel, GroupAggregateModel, UserAggregateModel
from .systemfields import (
    AccountStatusField,
    AccountVisibilityField,
    DomainCategoryNameField,
    DomainField,
    DomainOrgField,
    DomainStatusNameField,
    IsNotNoneField,
    UserIdentitiesField,
)

EmulatedPID = namedtuple("EmulatedPID", ["pid_value"])
"""Emulated PID"""


class AggregatePID:
    """Helper emulate a PID field."""

    def __init__(self, pid_field):
        """Constructor."""
        self._pid_field = pid_field

    def __get__(self, record, owner=None):
        """Evaluate the property."""
        if record is None:
            return GetRecordResolver(owner)
        return EmulatedPID(record[self._pid_field])


class GetRecordResolver(object):
    """Resolver that simply uses get record."""

    def __init__(self, record_cls):
        """Initialize resolver."""
        self._record_cls = record_cls

    def resolve(self, pid_value):
        """Simply get the record."""
        return self._record_cls.get_record(pid_value)


class BaseAggregate(Record):
    """An aggregate of information about a user group/role."""

    metadata = None
    """Disabled metadata field from the base class."""

    def __getitem__(self, name):
        """Get a dict key item."""
        try:
            return getattr(self.model, name)
        except AttributeError:
            raise KeyError(name)

    def __repr__(self):
        """Create string representation."""
        return f"<{self.__class__.__name__}: {self.model.data}>"

    def __unicode__(self):
        """Create string representation."""
        return self.__repr__()

    @classmethod
    def from_model(cls, sa_model):
        """Create an aggregate from an SQL Alchemy model."""
        return cls({}, model=cls.model_cls(model_obj=sa_model))

    def _validate(self, *args, **kwargs):
        """Skip the validation."""
        pass

    def commit(self):
        """Update the aggregate data on commit."""
        # You can only commit if you have an underlying model object.
        if self.model._model_obj is None:
            raise ValueError(f"{self.__class__.__name__} not backed by a model.")
        if self.model._model_obj not in db.session:
            with db.session.begin_nested():
                # make sure we get an id assigned
                db.session.add(self.model._model_obj)
        # Basically re-parses the model object.
        model = self.model_cls(model_obj=self.model._model_obj)
        self.model = model
        return self


def _validate_user_data(user_data):
    """Validate the entered data for the user creation.

    This is a special case for validation done outside of the schema because it requires
    database queries that can significantly slow down serialization. We want to perform
    this validation upon account creation.
    Also, we can't let this fail naturaly at the DB level because it will happen during the
    `commit` state of the UOW and the feedback to the form can't be sent.
    """
    errors = {}
    username = user_data["username"]
    email = user_data["email"]
    # Check if Email exists already
    existing_email = db.session.query(User).filter_by(email=email).first()
    if existing_email:
        errors["email"] = [_("Email already used by another account.")]
    # Check if Username exists already
    existing_username = db.session.query(User).filter_by(username=username).first()
    if existing_username:
        errors["username"] = [_("Username already used by another account.")]
    if errors:
        raise ValidationError(errors)


class UserAggregate(BaseAggregate):
    """An aggregate of information about a user."""

    model_cls = UserAggregateModel
    """The model class for the request."""

    # NOTE: the "uuid" isn't a UUID but contains the same value as the "id"
    #       field, which is currently an integer for User objects!
    dumper = SearchDumper(
        extensions=[
            EmailFieldDumperExt("email"),
            IndexedAtDumperExt(),
        ],
        model_fields={
            "id": ("uuid", int),
        },
    )
    """Search dumper with configured extensions."""

    index = IndexField("users-user-v3.0.0", search_alias="users")
    """The search engine index to use."""

    id = ModelField("id", dump_type=int)
    """The user identifier."""

    active = ModelField("active", dump_type=bool)
    """Determine is user is active and can login."""

    # Profile fields
    username = ModelField("username", dump_type=str)
    """The user's email address."""

    email = ModelField("email", dump_type=str)
    """The user's email address."""

    domain = ModelField("domain", dump_type=str)
    """The domain of the users' email address."""

    profile = ModelField("profile", dump_type=dict)
    """The user's profile."""

    preferences = ModelField("preferences", dump_type=dict)
    """User preferences."""

    # Timestamps fields
    confirmed_at = ModelField("confirmed_at", dump_type=datetime)
    """Timestamp for when account was confirmed."""

    verified_at = ModelField("verified_at", dump_type=datetime)
    """Timestamp for when account was verified."""

    blocked_at = ModelField("blocked_at", dump_type=datetime)
    """Timestamp for when account was blocked."""

    current_login_at = ModelField("current_login_at", dump_type=datetime)
    """Timestamp for when account was blocked."""

    confirmed = IsNotNoneField("confirmed_at", index=True)
    """Boolean to determine if verified."""

    verified = IsNotNoneField("verified_at", index=True)
    """Boolean to determine if verified."""

    blocked = IsNotNoneField("blocked_at", index=True)
    """Boolean to determine if verified."""

    # Status fields
    status = AccountStatusField(index=True)
    """Combined account status attribute."""

    visibility = AccountVisibilityField(index=True)
    """Combined profile visibility attribute."""

    domaininfo = DomainField(use_cache=True, index=True)
    """Domain information."""

    identities = UserIdentitiesField("identities", use_cache=True, index=True)
    """User identities."""

    @property
    def avatar_chars(self):
        """Get avatar characters for user."""
        text = None
        if self.profile.get("full_name"):
            text = self.profile["full_name"]
        elif self.username:
            text = self.username
        else:
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVXYZ"
            text = alphabet[self.id % len(alphabet)]

        return text[0].upper()

    @property
    def avatar_color(self):
        """Get avatar color for user."""
        colors = current_app.config["USERS_RESOURCES_AVATAR_COLORS"]
        return colors[self.id % len(colors)]

    @classmethod
    def create(cls, data, id_=None, validator=None, format_checker=None, **kwargs):
        """Create a new User and store it in the database."""
        try:
            # Check if email and  username already exists by another account.
            _validate_user_data(data)
            # Create User
            account_user = current_datastore.create_user(**data)
            return cls.from_model(account_user)
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(message=f"Unexpected Issue: {str(e)}", data=data)

    def verify(self):
        """Activates the current user.

        Activation of the user is proxied through the datastore.
        """
        user = self.model.model_obj
        if user is None:
            return False
        return current_datastore.verify_user(user)

    def block(self):
        """Blocks a user."""
        user = self.model.model_obj
        if user is None:
            return False
        return current_datastore.block_user(user)

    def activate(self):
        """Activate a previously deactivated user."""
        user = self.model.model_obj
        if user is None:
            return False
        return current_datastore.activate_user(user)

    def deactivate(self):
        """Deactivates the current user."""
        user = self.model.model_obj
        if user is None:
            return False
        return current_datastore.deactivate_user(user)

    @classmethod
    def get_record(cls, id_):
        """Get the user via the specified ID."""
        with db.session.no_autoflush:
            # Notifications builders right now manage to pass "system" as an
            # id when they try use the ServiceResultResolvers on
            # {'user': 'system'} which results in a database transaction being
            # rolled back when quering on an integer id column with a string.
            if id_ == "system":
                return None

            user = current_datastore.get_user_by_id(id_)
        if user is None:
            return None

        with db.session.no_autoflush:
            return cls.from_model(user)


class GroupAggregate(BaseAggregate):
    """An aggregate of information about a user group/role."""

    model_cls = GroupAggregateModel
    """The model class for the user group aggregate."""

    # NOTE: the "uuid" isn't a UUID but contains the same value as the "id"
    #       field, which is currently a str for Role objects (role.name)!
    dumper = SearchDumper(extensions=[], model_fields={"id": ("uuid", str)})
    """Search index dumper."""

    index = IndexField("groups-group-v2.0.0", search_alias="groups")
    """The search engine index to use."""

    id = ModelField("id", dump_type=str)
    """ID of group."""

    name = ModelField("name", dump_type=str)
    """The group's name."""

    description = ModelField("description", dump_type=str)
    """The group's description."""

    is_managed = ModelField("is_managed", dump_type=bool)
    """If the group is managed manually."""

    @property
    def avatar_chars(self):
        """Get avatar characters for user."""
        return self.id[0].upper()

    @property
    def avatar_color(self):
        """Get avatar color for user."""
        colors = current_app.config["USERS_RESOURCES_AVATAR_COLORS"]
        normalized_group_initial = unicodedata.normalize("NFKD", self.id[0]).encode(
            "ascii", "ignore"
        )
        return colors[int(normalized_group_initial, base=36) % len(colors)]

    @classmethod
    def get_record(cls, id_):
        """Get the user group via the specified ID."""
        # TODO how do we want to resolve the roles? via ID or name?
        with db.session.no_autoflush:
            role = db.session.get(current_datastore.role_model, id_)
            if role is None:
                return None
            return cls.from_model(role)

    @classmethod
    def get_record_by_name(cls, name):
        """Get the user group via the specified ID."""
        # TODO how do we want to resolve the roles? via ID or name?
        with db.session.no_autoflush:
            role = (
                db.session.query(current_datastore.role_model)
                .filter_by(name=name)
                .one_or_none()
            )
            if role is None:
                return None
            return cls.from_model(role)


class OrgNameDumperExt(SearchDumperExt):
    """Custom fields dumper extension."""

    def dump(self, record, data):
        """Dump for faceting."""
        org = data.get("org", None)
        if org and len(org) > 0:
            data["org_names"] = [o["name"] for o in org]

    def load(self, data, record_cls):
        """Remove data from object."""
        data.pop("org_names", None)


class DomainAggregate(BaseAggregate):
    """An aggregate of information about a user."""

    model_cls = DomainAggregateModel
    """The model class for the request."""

    # NOTE: the "uuid" isn't a UUID but contains the same value as the "id"
    #       field, which is currently an integer for User objects!
    dumper = SearchDumper(
        extensions=[
            IndexedAtDumperExt(),
            OrgNameDumperExt(),
        ],
        model_fields={
            "id": ("uuid", int),
        },
    )
    """Search dumper with configured extensions."""

    index = IndexField("domains-domain-v1.0.0", search_alias="domains")
    """The search engine index to use."""

    pid = AggregatePID("domain")
    """Needed to emulate pid access."""

    id = ModelField("id", dump_type=int)
    """The user identifier."""

    domain = ModelField("domain", dump_type=str)
    """The domain of the users' email address."""

    tld = ModelField("tld", dump_type=str)
    """Top level domain."""

    status = ModelField("status", dump_type=int)
    """Domain status."""

    status_name = DomainStatusNameField(index=True)
    """Domain status name."""

    flagged = ModelField("flagged", dump_type=bool)
    """Flagged."""

    flagged_source = ModelField("flagged_source", dump_type=str)
    """Source of flagging."""

    category = ModelField("category", dump_type=int)
    """Domain category."""

    category_name = DomainCategoryNameField(use_cache=True, index=True)
    """Domain category name."""

    org_id = ModelField("org_id", dump_type=int)
    """Number of users."""

    org = DomainOrgField("org", use_cache=True, index=True)
    """Organization behind the domain."""

    num_users = ModelField("num_users", dump_type=int)
    """Number of users."""

    num_active = ModelField("num_active", dump_type=int)
    """Number of active users."""

    num_inactive = ModelField("num_inactive", dump_type=int)
    """Number of inactive users."""

    num_confirmed = ModelField("num_confirmed", dump_type=int)
    """Number of confirmed users."""

    num_verified = ModelField("num_verified", dump_type=int)
    """Number of verified users."""

    num_blocked = ModelField("num_blocked", dump_type=int)
    """Number of blocked users."""

    @classmethod
    def get_record(cls, id_):
        """Get the user via the specified ID."""
        with db.session.no_autoflush:
            domain = current_datastore.find_domain(id_)
        if domain is None:
            raise NoResultFound()
        return cls.from_model(domain)

    @classmethod
    def create(cls, data, id_=None, **kwargs):
        """Create a domain."""
        return DomainAggregate(data, model=DomainAggregateModel(model_obj=Domain()))

    def delete(self, force=True):
        """Delete the domain."""
        db.session.delete(self.model.model_obj)
