# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Base model classes for user and group management in Invenio."""

from abc import ABC, abstractmethod

from flask import current_app
from invenio_accounts.proxies import current_datastore
from invenio_accounts.utils import DomainStatus
from invenio_db import db


class AggregateMetadata(ABC):
    """Model class that does not corresponds to a database table.

    Since we already have all information about the required entities
    stored in the database and just want to provide a central API to
    manage these entities as one, we do not want to store any of the
    information in the database again.
    Instead, we provide a mock model that provides the model interface
    that's expected by API classes as far as necessary.
    """

    _properties = []
    """Properties of this object that can be accessed."""

    _set_properties = []
    """Properties of this object that can be set."""

    _data = None

    def __init__(self, model_obj=None, **kwargs):
        """Constructor."""
        super().__setattr__("_data", {})
        if model_obj is not None:
            # E.g. when data is loaded from database
            self.from_model(model_obj)
            super().__setattr__("_model_obj", model_obj)
        else:
            # E.g. when data is loaded from the search index
            self.from_kwargs(kwargs)
            super().__setattr__("_model_obj", None)

    @property
    @abstractmethod
    def model_obj(self):
        """The actual model object behind this mock model."""
        return None

    def from_kwargs(self, kwargs):
        """Extract information from kwargs."""
        for p in self._properties:
            self._data[p] = kwargs.get(p, None)

    def from_model(self, model_obj):
        """Extract information from a user/role object."""
        # Edit self._properties if you need to add more properties
        for p in self._properties:
            self._data[p] = getattr(model_obj, p, None)

    def __getattr__(self, name):
        """Get an attribute from the model."""
        if name in self._properties:
            return self._data[name]
        else:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        """Set an attribute from the model."""
        if name not in self._set_properties:
            raise AttributeError(name)
        super().__setattr__(name, value)
        setattr(self.model_obj, name, value)

    # Methods required to make it a record.
    @property
    def is_deleted(self):
        """Method needed for the record API."""
        return False

    @property
    def json(self):
        """Method needed for the record API."""
        return {p: getattr(self, p, None) for p in self._properties}

    @property
    def data(self):
        """Method needed for the record API."""
        return {p: getattr(self, p, None) for p in self._properties}


class UserAggregateModel(AggregateMetadata):
    """User aggregate data model."""

    # If you add properties here you likely also want to add a ModelField on
    # the UserAggregate API class.
    _properties = [
        "id",
        "version_id",
        "email",
        "domain",
        "username",
        "active",
        "preferences",
        "profile",
        "confirmed_at",
        "blocked_at",
        "verified_at",
        "created",
        "updated",
        "current_login_at",
    ]
    """Properties of this object that can be accessed."""

    _set_properties = [
        "active",
        "blocked_at",
        "confirmed_at",
        "verified_at",
    ]
    """Properties of this object that can be set."""

    def from_model(self, user):
        """Extract information from a user object."""
        super().from_model(user)
        self._data["profile"] = dict(user.user_profile or {})

        # Set defaults
        self._data["preferences"] = dict(self._data["preferences"] or {})
        self._data["preferences"].setdefault("visibility", "restricted")
        self._data["preferences"].setdefault("email_visibility", "restricted")
        default_locale = current_app.config.get("BABEL_DEFAULT_LOCALE", "en")
        self._data["preferences"].setdefault("locale", default_locale)
        self._data["preferences"].setdefault("timezone", "Europe/Zurich")
        self._data["preferences"].setdefault(
            "notifications",
            {
                "enabled": True,
            },
        )

    @property
    def model_obj(self):
        """The actual model object behind this user aggregate."""
        if self._model_obj is None:
            id_ = self._data.get("id")
            with db.session.no_autoflush:
                self._model_obj = current_datastore.get_user_by_id(id_)
        return self._model_obj


class GroupAggregateModel(AggregateMetadata):
    """Mock model for glueing together various parts of user group info."""

    _properties = [
        "id",
        "version_id",
        "name",
        "description",
        "is_managed",
        "created",
        "updated",
    ]
    """Properties of this object that can be accessed."""

    _set_properties = []
    """Properties of this object that can be set."""

    @property
    def model_obj(self):
        """The actual model object behind this mock model."""
        if self._model_obj is None:
            name = self.data.get("id")
            with db.session.no_autoflush:
                self._model_obj = current_datastore.find_role(name)
        return self._model_obj


class DomainAggregateModel(AggregateMetadata):
    """Mock model for glueing together various parts of user group info."""

    _properties = [
        "category",
        "created",
        "domain",
        "flagged_source",
        "flagged",
        "id",
        "num_active",
        "num_blocked",
        "num_confirmed",
        "num_inactive",
        "num_users",
        "num_verified",
        "org_id",
        "status",
        "tld",
        "updated",
        "version_id",
    ]
    """Properties of this object that can be accessed."""

    _set_properties = [
        "category",
        "domain",
        "flagged_source",
        "flagged",
        "org_id",
        "status",
        "tld",
    ]
    """Properties of this object that can be set."""

    def from_model(self, domain):
        """Extract information from a user object."""
        super().from_model(domain)
        # Hardcoding version id to 1 since domain model doesn't have
        # a version id because we update the table often outside
        # of sqlalchemy ORM.
        self._data["version_id"] = 1
        # Convert enum
        status = self._data.get("status", None)
        if status and isinstance(status, DomainStatus):
            self._data["status"] = status.value

    @property
    def model_obj(self):
        """The actual model object behind this mock model."""
        if self._model_obj is None:
            domain = self.data.get("domain")
            with db.session.no_autoflush:
                self._model_obj = current_datastore.find_domain(domain)
        return self._model_obj
