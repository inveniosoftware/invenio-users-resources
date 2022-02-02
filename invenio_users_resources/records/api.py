# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""API classes for user and group management in Invenio."""


from invenio_accounts.proxies import current_datastore
from invenio_db import db
from invenio_records.dumpers import ElasticsearchDumper
from invenio_records.systemfields import ConstantField, DictField, ModelField
from invenio_records_resources.records.api import Record
from invenio_records_resources.records.systemfields import IndexField

from .models import UserAggregateModel, UserGroupAggregateModel


def parse_user_data(user):
    """Parse the user's information into a dictionary."""
    data = {
        "id": user.id,
        "email": user.email,
        "username": None,
        "full_name": None,
    }

    if user.profile is not None:
        data["full_name"] = user.profile.full_name
        data["username"] = user.profile.username
        # TODO populate more when we have extensible user profiles

    return data


def parse_role_data(role):
    """Parse the role's information into a dictionary."""
    data = {"id": role.id, "name": role.name, "description": role.description}
    return data


class UserAggregate(Record):
    """An aggregate of information about a user."""

    model_cls = UserAggregateModel
    """The model class for the request."""

    # NOTE: the "uuid" isn't a UUID but contains the same value as the "id"
    #       field, which is currently an integer for User objects!
    dumper = ElasticsearchDumper(
        extensions=[], model_fields={"id": ("uuid", int)}
    )
    """Elasticsearch dumper with configured extensions."""

    metadata = None
    """Disabled metadata field from the base class."""

    schema = ConstantField("$schema", "local://users/user-v1.0.0.json")
    """The JSON Schema to use for validation."""

    index = IndexField("users-user-v1.0.0", search_alias="users")
    """The Elasticsearch index to use."""

    # TODO
    id = ModelField("id")
    """The data-layer id."""

    email = DictField("email")
    """The user's email address."""

    username = DictField("username")
    """The user's username."""

    full_name = DictField("full_name")
    """The user's full name."""

    _user = None
    """The cached User entity."""

    @property
    def user(self):
        """Cache for the associated user object."""
        user = self._user
        if user is None:
            id_, email = self.id, self.email
            user = current_datastore.get_user(id_ or email)

            self._user = user

        return user

    @classmethod
    def create(
        cls, data, id_=None, validator=None, format_checker=None, **kwargs
    ):
        # NOTE: we don't use an actual database table, and as such can't
        #       use db.session.add(record.model)
        # TODO: should we do some JSON Schema validation here?
        #       or do we rely on marshmallow?
        with db.session.begin_nested():
            email = data["email"]
            active = data.pop("active", True)

            full_name = data.pop("full_name", None)
            username = data.pop("username", None)

            # TODO populate user profile
            if full_name and username:
                pass

            user = current_datastore.create_user(email=email, active=active)
            user_aggregate = cls.from_user(user)

            return user_aggregate

    def _validate(self, *args, **kwargs):
        """Skip the validation."""
        # TODO does a JSONSchema even make sense? we don't actually store
        #      anything, we just collect data from all over the place
        pass

    def commit(self):
        """Update the aggregate data on commit."""
        # TODO this does not allow us to set properties via the UserAggregate?
        #      because everything's taken from the User object...
        data = parse_user_data(self.user)
        self.update(data)
        self.model.update(data)
        return self

    @classmethod
    def from_user(cls, user):
        """Create the user aggregate from the given user."""
        # TODO
        data = parse_user_data(user)

        model = cls.model_cls(data)
        user_agg = cls(data, model=model)
        user_agg._user = user
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


class UserGroupAggregate(Record):
    """An aggregate of information about a user group/role."""

    model_cls = UserGroupAggregateModel
    """The model class for the user group aggregate."""

    # NOTE: the "uuid" isn't a UUID but contains the same value as the "id"
    #       field, which is currently an integer for Role objects!
    dumper = ElasticsearchDumper(
        extensions=[], model_fields={"id": ("uuid", int)}
    )

    metadata = None
    """Disabled metadata field from the base class."""

    schema = ConstantField("$schema", "local://users/group-v1.0.0.json")
    """The JSON Schema to use for validation."""

    index = IndexField("user_groups-group-v1.0.0", search_alias="user_groups")
    """The Elasticsearch index to use."""

    # TODO
    id = ModelField("id")
    """The data-layer id."""

    name = DictField("name")
    """The group's name."""

    description = DictField("description")
    """The group's description."""

    _role = None
    """The cached Role entity."""

    @property
    def role(self):
        """Cache for the associated role object."""
        role = self._role
        if role is None:
            if self.id is not None:
                role = current_datastore.role_model.query.get(self.id)

            if role is None and self.name is not None:
                role = current_datastore.find_role(self.name)

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

        model = cls.model_cls(data)
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
