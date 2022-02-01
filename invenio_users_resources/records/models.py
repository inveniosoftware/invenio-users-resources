# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Base model classes for user and group management in Invenio."""

import uuid

from invenio_accounts.models import Role, User
from invenio_db import db
from invenio_records.models import RecordMetadataBase
from sqlalchemy.types import Integer
from sqlalchemy_utils import UUIDType


class MockModel(dict):
    """Model class that does not correspondond to a database table.

    Since we already have all information about the required entities
    stored in the database and just want to provide a central API to
    manage these entities as one, we do not want to store any of the
    information in the database again.
    Instead, we provide a mock model that provides the model interface
    that's expected by API classes as far as necessary.
    """

    def __init__(self, data=None, **kwargs):
        """Constructor."""
        data.update(kwargs)
        super().__init__(data)

    @property
    def id(self):
        return self.data["id"]

    @property
    def created(self):
        # TODO utcnow?
        return None

    @property
    def updated(self):
        # TODO same as above
        return None

    @property
    def data(self):
        return dict(self)

    @property
    def json(self):
        return dict(self)

    @property
    def version_id(self):
        # TODO
        return 1

    @property
    def is_deleted(self):
        # TODO
        return False


class UserAggregateModel(MockModel):
    """Mock model for glueing together various parts of user info."""


class UserGroupAggregateModel(MockModel):
    """Mock model for glueing together various parts of user group info."""
