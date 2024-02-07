# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""API classes for user and group management in Invenio."""

import unicodedata
from datetime import datetime

from flask import current_app
from invenio_accounts.proxies import current_datastore
from invenio_db import db
from invenio_records.dumpers import SearchDumper
from invenio_records.dumpers.indexedat import IndexedAtDumperExt
from invenio_records.systemfields import ModelField
from invenio_records_resources.records.api import Record
from invenio_records_resources.records.systemfields import IndexField

from .dumpers import EmailFieldDumperExt
from .models import GroupAggregateModel, UserAggregateModel
from .systemfields import (
    AccountStatusField,
    AccountVisibilityField,
    DomainField,
    IsNotNoneField,
    UserIdentitiesField,
)


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
        # Basically re-parses the model object.
        model = self.model_cls(model_obj=self.model._model_obj)
        self.model = model
        return self


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

    index = IndexField("users-user-v2.0.0", search_alias="users")
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
        # NOTE: we don't use an actual database table, and as such can't
        #       use db.session.add(record.model)
        with db.session.begin_nested():
            # create_user() will already take care of creating the profile
            # for us, if it's specified in the data
            user = current_datastore.create_user(**data)
            return cls.from_model(user)

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
            role = current_datastore.role_model.query.get(id_)
            if role is None:
                return None
            return cls.from_model(role)

    @classmethod
    def get_record_by_name(cls, name):
        """Get the user group via the specified ID."""
        # TODO how do we want to resolve the roles? via ID or name?
        with db.session.no_autoflush:
            role = current_datastore.role_model.query.filter_by(name=name).one_or_none()
            if role is None:
                return None
            return cls.from_model(role)
