# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.
See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""


import pytest
from flask_principal import Identity, Need, UserNeed
from flask_security import login_user
from flask_security.utils import hash_password
from invenio_access.models import ActionRoles
from invenio_access.permissions import superuser_access
from invenio_accounts.models import Role
from invenio_accounts.testutils import login_user_via_session
from invenio_app.factory import create_api as _create_api


@pytest.fixture(scope="module")
def celery_config():
    """Override pytest-invenio fixture.
    TODO: Remove this fixture if you add Celery support.
    """
    return {}


@pytest.fixture(scope="module")
def app_config(app_config):
    """Mimic an instance's configuration."""
    app_config["JSONSCHEMAS_HOST"] = "localhost"
    app_config["BABEL_DEFAULT_LOCALE"] = "en"
    # app_config["I18N_LANGUAGES"] = [('da', 'Danish')]
    app_config[
        "RECORDS_REFRESOLVER_CLS"
    ] = "invenio_records.resolver.InvenioRefResolver"
    app_config[
        "RECORDS_REFRESOLVER_STORE"
    ] = "invenio_jsonschemas.proxies.current_refresolver_store"
    app_config["REQUESTS_REGISTERED_TYPES"] = [DefaultRequestType()]
    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return _create_api


@pytest.fixture(scope="module")
def identity_simple():
    """Simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method="system_role", value="any_user"))
    i.provides.add(Need(method="system_role", value="authenticated_user"))
    return i


@pytest.fixture(scope="module")
def identity_simple_2():
    """Another simple identity fixture."""
    i = Identity(2)
    i.provides.add(UserNeed(2))
    i.provides.add(Need(method="system_role", value="any_user"))
    i.provides.add(Need(method="system_role", value="authenticated_user"))
    return i


@pytest.fixture(scope="module")
def identity_stranger():
    """An unrelated user identity fixture."""
    i = Identity(4)
    i.provides.add(UserNeed(4))
    i.provides.add(Need(method="system_role", value="any_user"))
    return i




# Resource layer fixtures
@pytest.fixture()
def headers():
    """Default headers for making requests."""
    return {
        "content-type": "application/json",
        "accept": "application/json",
    }


@pytest.fixture(scope="module")
def users(app):
    """Create example users."""
    # This is a convenient way to get a handle on db that, as opposed to the
    # fixture, won't cause a DB rollback after the test is run in order
    # to help with test performance (creating users is a module -if not higher-
    # concern)
    from invenio_db import db

    with db.session.begin_nested():
        datastore = app.extensions["security"].datastore

        su_role = Role(name="superuser-access")
        db.session.add(su_role)

        su_action_role = ActionRoles.create(action=superuser_access, role=su_role)
        db.session.add(su_action_role)

        user1 = datastore.create_user(
            email="user1@example.org", password=hash_password("password"), active=True
        )
        user2 = datastore.create_user(
            email="user2@example.org", password=hash_password("password"), active=True
        )
        admin = datastore.create_user(
            email="admin@example.org", password=hash_password("password"), active=True
        )
        admin.roles.append(su_role)

    db.session.commit()
    return [user1, user2, admin]


@pytest.fixture()
def example_user(users):
    """Create example user."""
    return users[0]

@pytest.fixture()
def example_fullname_user(users)
    users[1].profile.full_name = "Full Name"
    return users[1]

@pytest.fixture()
def client_logged_as(client, users):
    """Logs in a user to the client."""

    def log_user(user_email):
        """Log the user."""
        user = next((u for u in users if u.email == user_email), None)
        login_user(user, remember=True)
        login_user_via_session(client, email=user_email)
        return client

    return log_user


@pytest.fixture(scope="module")
def groups(app):
    """Create example groups."""
    # This is a convenient way to get a handle on db that, as opposed to the
    # fixture, won't cause a DB rollback after the test is run in order
    # to help with test performance
    from invenio_db import db

    with db.session.begin_nested():
        datastore = app.extensions["security"].datastore

        su_role = Role(name="superuser-access")
        db.session.add(su_role)

        su_action_role = ActionRoles.create(action=superuser_access, role=su_role)
        db.session.add(su_action_role)

        group1 = datastore.create_group(
            name="group1", description="a group for testing", role=None
        )

        group2 = datastore.create_group(
        name="SecondGroup", descriptio="another group for testing", role=None
        )
    db.session.commit()
    return [group1, group2]

@pytest.fixture()
def example_group(groups):
    """Create example group."""
    return groups[0]
