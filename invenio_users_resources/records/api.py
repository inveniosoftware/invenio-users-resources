# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""API classes for user and group management in Invenio."""
import random
import unicodedata

from flask import current_app
from invenio_accounts.proxies import current_datastore
from invenio_db import db
from invenio_records.dumpers import SearchDumper
from invenio_records.systemfields import DictField, ModelField
from invenio_records_resources.records.api import Record
from invenio_records_resources.records.systemfields import IndexField

from .dumpers import EmailFieldDumperExt
from .models import GroupAggregateModel, UserAggregateModel


def parse_user_data(user):
    """Parse the user's information into a dictionary."""
    data = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "active": user.active,
        "confirmed": user.confirmed_at is not None,
        "preferences": dict(user.preferences or {}),
        "profile": dict(user.user_profile or {}),
    }

    data["preferences"].setdefault("visibility", "restricted")
    data["preferences"].setdefault("email_visibility", "restricted")
    return data


def parse_role_data(role):
    """Parse the role's information into a dictionary."""
    data = {
        "id": role.name,  # due to flask security exposing user id
        "name": role.description,
        "is_managed": True,  # TODO
    }
    return data


class UserAggregate(Record):
    """An aggregate of information about a user."""

    model_cls = UserAggregateModel
    """The model class for the request."""

    # NOTE: the "uuid" isn't a UUID but contains the same value as the "id"
    #       field, which is currently an integer for User objects!
    dumper = SearchDumper(
        extensions=[EmailFieldDumperExt("email")],
        model_fields={"id": ("uuid", int)},
    )
    """Search dumper with configured extensions."""

    metadata = None
    """Disabled metadata field from the base class."""

    index = IndexField("users-user-v1.0.0", search_alias="users")
    """The search engine index to use."""

    # TODO
    id = ModelField("id")
    """The data-layer id."""

    email = DictField("email")
    """The user's email address."""

    username = DictField("username")
    """The user's email address."""

    profile = DictField("profile")
    """The user's profile."""

    active = DictField("active")

    confirmed = DictField("confirmed")

    preferences = DictField("preferences")

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
            user_aggregate = cls.from_user(user)
            return user_aggregate

    def _validate(self, *args, **kwargs):
        """Skip the validation."""
        pass

    def commit(self):
        """Update the aggregate data on commit."""
        # TODO this does not allow us to set properties via the UserAggregate?
        #      because everything's taken from the User object...
        data = parse_user_data(self.model.model_obj)
        self.update(data)
        self.model.update(data)
        return self

    @classmethod
    def from_user(cls, user):
        """Create the user aggregate from the given user."""
        # TODO
        data = parse_user_data(user)

        model = cls.model_cls(data, model_obj=user)
        user_agg = cls(data, model=model)
        return user_agg

    @classmethod
    def get_record(cls, id_):
        """Get the user via the specified ID."""
        # TODO the the datastore.get_user() method will resolve both
        #      ID as well as email, which we do not necessarily want
        user = current_datastore.get_user(id_)
        if user is None:
            return None

        return cls.from_user(user)


class GroupAggregate(Record):
    """An aggregate of information about a user group/role."""

    model_cls = GroupAggregateModel
    """The model class for the user group aggregate."""

    # NOTE: the "uuid" isn't a UUID but contains the same value as the "id"
    #       field, which is currently a str for Role objects (role.name)!
    dumper = SearchDumper(extensions=[], model_fields={"id": ("uuid", str)})

    metadata = None
    """Disabled metadata field from the base class."""

    index = IndexField("groups-group-v1.0.0", search_alias="groups")
    """The search engine index to use."""

    # TODO
    id = ModelField("id")
    """The data-layer id."""

    name = DictField("name")
    """The group's name."""

    is_managed = DictField("is_managed")
    """If the group is managed manually."""

    _role = None
    """The cached Role entity."""

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

    @property
    def role(self):
        """Cache for the associated role object."""
        role = self._role
        if role is None:
            if role is None and self.id is not None:
                role = current_datastore.find_role(self.id)

            self._role = role

        return role

    def commit(self):
        """Update the aggregate data on commit."""
        # TODO this does not allow us to set properties via the aggregate?
        #      because everything's taken from the Role object...
        data = parse_role_data(self.role)
        self.update(data)
        self.model.update(data)
        return self

    @classmethod
    def from_role(cls, role):
        """Create the user group aggregate from the given role."""
        # TODO
        data = parse_role_data(role)

        model = cls.model_cls(data, model_obj=role)
        role_agg = cls(data, model=model)
        role_agg._role = role
        return role_agg

    @classmethod
    def get_record(cls, id_):
        """Get the user group via the specified ID."""
        # TODO how do we want to resolve the roles? via ID or name?
        role = current_datastore.role_model.query.get(id_)
        if role is None:
            return None

        return cls.from_role(role)

    @classmethod
    def get_record_by_name(cls, name):
        """Get the user group via the specified ID."""
        # TODO how do we want to resolve the roles? via ID or name?
        role = current_datastore.role_model.query.filter_by(name=name).one_or_none()
        if role is None:
            return None

        return cls.from_role(role)
