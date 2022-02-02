# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 European Union.
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

import pytest
from invenio_accounts.models import Role
from invenio_app.factory import create_api

from invenio_users_resources.proxies import (
    current_groups_service,
    current_users_service,
)

pytest_plugins = ("celery.contrib.pytest",)


#
# Application
#
@pytest.fixture(scope="module")
def app_config(app_config):
    """Override pytest-invenio app_config fixture."""
    app_config[
        "RECORDS_REFRESOLVER_CLS"
    ] = "invenio_records.resolver.InvenioRefResolver"
    app_config[
        "RECORDS_REFRESOLVER_STORE"
    ] = "invenio_jsonschemas.proxies.current_refresolver_store"
    # Variable not used. We set it to silent warnings
    app_config["JSONSCHEMAS_HOST"] = "not-used"

    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return create_api


@pytest.fixture()
def headers():
    """Default headers for making requests."""
    return {
        "content-type": "application/json",
        "accept": "application/json",
    }


#
# Services
#
@pytest.fixture(scope="module")
def user_service(app):
    """User service."""
    return current_users_service


@pytest.fixture(scope="module")
def group_service(app):
    """Group service."""
    return current_groups_service


#
# Users
#
@pytest.fixture(scope="module")
def users(UserFixture, app, database):
    """Test users."""
    users = {}
    for r in ["user1", "user2"]:
        u = UserFixture(
            email=f"{r}@{r}.org",
            password=r,
        )
        u.create(app, database)
        users[r] = u
    return users


@pytest.fixture(scope="module")
def group(database):
    """A single group."""
    r = Role(name="it-dep")
    database.session.add(r)
    database.session.commit()
    return r


@pytest.fixture(scope="module")
def user1(users):
    """User 1."""
    return users["user1"]


@pytest.fixture(scope="module")
def user2(users):
    """User 2."""
    return users["user2"]
