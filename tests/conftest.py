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
from flask_principal import AnonymousIdentity
from invenio_access.permissions import any_user as any_user_need
from invenio_accounts.proxies import current_datastore
from invenio_app.factory import create_api

from invenio_users_resources.proxies import (
    current_groups_service,
    current_users_service,
)
from invenio_users_resources.records import GroupAggregate, UserAggregate

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
def anon_identity():
    """A new user."""
    identity = AnonymousIdentity()
    identity.provides.add(any_user_need)
    return identity


@pytest.fixture(scope="module")
def users_data():
    """Data for users."""
    return [
        {
            "username": "pubres",
            "email": "pubres@inveniosoftware.org",
            "profile": {
                "full_name": "Tim Smith",
                "affiliations": "CERN",
            },
            "preferences": {
                "visibility": "public",
                "email_visibility": "restricted",
            },
        },
        {
            "username": "pub",
            "email": "pub@inveniosoftware.org",
            "profile": {
                "full_name": "Jose Benito Gonzalez Lopez",
                "affiliations": "CERN",
            },
            "preferences": {
                "visibility": "public",
                "email_visibility": "public",
            },
        },
        {
            "username": "res",
            "email": "res@inveniosoftware.org",
            "profile": {
                "full_name": "Donat Agosti",
                "affiliations": "Plazi",
            },
            "preferences": {
                "visibility": "restricted",
                "email_visibility": "restricted",
            },
        },
        {
            "username": "unconfirmed",
            "email": "unconfirmed@inveniosoftware.org",
            "confirmed": False,
        },
        {
            "username": "inactive",
            "email": "inactive@inveniosoftware.org",
            "profile": {
                "full_name": "Spammer",
                "affiliations": "Spam org",
            },
            "preferences": {
                "visibility": "public",
                "email_visibility": "public",
            },
            "active": False,
        },
    ]


@pytest.fixture(scope="module")
def users(UserFixture, app, database, users_data):
    """Test users."""
    users = {}
    for obj in users_data:
        u = UserFixture(
            username=obj["username"],
            email=obj["email"],
            password=obj["username"],
            user_profile=obj.get("profile"),
            preferences=obj.get("preferences"),
            active=obj.get("active", True),
            confirmed=obj.get("confirmed", True),
        )
        u.create(app, database)
        users[obj["username"]] = u
    UserAggregate.index.refresh()
    return users


def _create_group(name, description, database):
    """Creates a Role/Group."""
    r = current_datastore.create_role(name=name, description=description)
    current_datastore.commit()

    return r


@pytest.fixture(scope="module")
def group(database):
    """A single group."""
    r = _create_group(name="it-dep", description="IT Department", database=database)

    GroupAggregate.index.refresh()
    return r


@pytest.fixture(scope="module")
def groups(database, group):
    """A single group."""
    roles = [group]  # it-dep
    roles.append(
        _create_group(name="hr-dep", description="HR Department", database=database)
    )

    GroupAggregate.index.refresh()
    return roles


@pytest.fixture(scope="module")
def user_pub(users):
    """User jbenito (restricted/restricted)."""
    return users["pub"]


@pytest.fixture(scope="module")
def user_pubres(users):
    """User tjs (public/restricted)."""
    return users["pubres"]


@pytest.fixture(scope="module")
def user_res(users):
    """User agosti (restricted/restricted)."""
    return users["res"]


@pytest.fixture(scope="module")
def user_inactive(users):
    """Inactive user."""
    return users["inactive"]


@pytest.fixture(scope="module")
def user_unconfirmed(users):
    """Unconfirmed user."""
    return users["unconfirmed"]
