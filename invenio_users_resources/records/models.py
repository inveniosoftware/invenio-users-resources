# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Base model classes for user and group management in Invenio."""

from abc import ABC, abstractmethod

from invenio_accounts.proxies import current_datastore


class MockModel(dict, ABC):
    """Model class that does not correspondond to a database table.

    Since we already have all information about the required entities
    stored in the database and just want to provide a central API to
    manage these entities as one, we do not want to store any of the
    information in the database again.
    Instead, we provide a mock model that provides the model interface
    that's expected by API classes as far as necessary.
    """

    def __init__(self, data=None, model_obj=None, **kwargs):
        """Constructor."""
        data.update(kwargs)
        super().__init__(data)
        self._model_obj = model_obj

    @property
    @abstractmethod
    def model_obj(self):
        """The actual model object behind this mock model."""
        return None

    @property
    def id(self):
        """User identifier."""
        return self.data["id"]

    @property
    def created(self):
        """When the user was created."""
        return self.model_obj.created

    @property
    def updated(self):
        """When the user was last updated."""
        return self.model_obj.updated

    @property
    def version_id(self):
        """Used by SQLAlchemy for optimistic concurrency control."""
        return self.model_obj.version_id

    @property
    def data(self):
        """Get the user's data by decoding the JSON."""
        return dict(self)

    @property
    def json(self):
        """Provide the user's data as a JSON/dict blob."""
        return dict(self)

    @property
    def is_deleted(self):
        """Boolean flag to determine if a user is soft deleted."""
        # TODO
        return False

    @property
    def blocked_at(self):
        """Date when the user was blocked, if any."""
        return self.model_obj.blocked_at

    @blocked_at.setter
    def blocked_at(self, value):
        self.model_obj.blocked_at = value

    @property
    def verified_at(self):
        """Date when the user was verified, if any."""
        return self.model_obj.verified_at

    @verified_at.setter
    def verified_at(self, value):
        self.model_obj.verified_at = value

    @property
    def active(self):
        """Boolean flag to determine if a user is active."""
        return self.model_obj.active

    @active.setter
    def active(self, value):
        self.model_obj.active = value


class UserAggregateModel(MockModel):
    """Mock model for glueing together various parts of user info."""

    @property
    def model_obj(self):
        """The actual model object behind this mock model."""
        if self._model_obj is None:
            id_ = self.data.get("id")
            email = self.data.get("email")
            self._model_obj = current_datastore.get_user(id_ or email)
        return self._model_obj


class GroupAggregateModel(MockModel):
    """Mock model for glueing together various parts of user group info."""

    @property
    def model_obj(self):
        """The actual model object behind this mock model."""
        if self._model_obj is None:
            name = self.data.get("id")
            self._model_obj = current_datastore.find_role(name)
        return self._model_obj
