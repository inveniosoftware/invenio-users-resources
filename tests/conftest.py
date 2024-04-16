# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 European Union.
# Copyright (C) 2022-2024 CERN.
# Copyright (C) 2023 Graz University of Technology.
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
from invenio_access.models import ActionRoles
from invenio_access.permissions import any_user as any_user_need
from invenio_access.permissions import system_identity
from invenio_accounts.models import Domain, DomainCategory, DomainOrg, Role
from invenio_accounts.proxies import current_datastore
from invenio_app.factory import create_api
from invenio_cache.proxies import current_cache
from marshmallow import fields

from invenio_users_resources.permissions import user_management_action
from invenio_users_resources.proxies import (
    current_domains_service,
    current_groups_service,
    current_users_service,
)
from invenio_users_resources.records import GroupAggregate
from invenio_users_resources.services.schemas import (
    NotificationPreferences,
    UserPreferencesSchema,
)

pytest_plugins = ("celery.contrib.pytest",)


class UserPreferencesNotificationsSchema(UserPreferencesSchema):
    """Schema extending preferences with notification preferences."""

    notifications = fields.Nested(NotificationPreferences)


#
# Application
#
@pytest.fixture(scope="module")
def app_config(app_config):
    """Override pytest-invenio app_config fixture."""
    app_config["RECORDS_REFRESOLVER_CLS"] = (
        "invenio_records.resolver.InvenioRefResolver"
    )
    app_config["RECORDS_REFRESOLVER_STORE"] = (
        "invenio_jsonschemas.proxies.current_refresolver_store"
    )
    # Variable not used. We set it to silent warnings
    app_config["JSONSCHEMAS_HOST"] = "not-used"
    # setting preferences schema to test notifications
    app_config["ACCOUNTS_USER_PREFERENCES_SCHEMA"] = UserPreferencesNotificationsSchema

    app_config["USERS_RESOURCES_GROUPS_ENABLED"] = True

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
def user_moderator(UserFixture, app, database, users):
    """Admin user for requests."""
    action_name = user_management_action.value
    moderator = users["user_moderator"]

    role = Role(name=action_name)
    database.session.add(role)

    action_role = ActionRoles.create(action=user_management_action, role=role)
    database.session.add(action_role)

    moderator.user.roles.append(role)
    database.session.commit()
    return moderator


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
        {
            "username": "notification_enabled",
            "email": "notification-enabled@inveniosoftware.org",
            "profile": {
                "full_name": "Mr. Worldwide",
                "affiliations": "World",
            },
            "preferences": {
                "visibility": "restricted",
                "email_visibility": "public",
                "notifications": {
                    "enabled": True,
                },
            },
        },
        {
            "username": "notification_disabled",
            "email": "notification-disabled@inveniosoftware.org",
            "profile": {
                "full_name": "Loner",
                "affiliations": "Home",
            },
            "preferences": {
                "visibility": "restricted",
                "email_visibility": "public",
                "notifications": {
                    "enabled": False,
                },
            },
        },
        {
            "username": "user_moderator",
            "email": "user_moderator@inveniosoftware.org",
            "profile": {
                "full_name": "Mr",
                "affiliations": "Admin",
            },
            "preferences": {
                "visibility": "restricted",
                "email_visibility": "public",
                "notifications": {
                    "enabled": False,
                },
            },
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
    current_users_service.indexer.process_bulk_queue()
    current_users_service.record_cls.index.refresh()
    database.session.commit()
    return users


def _create_group(id, name, description, is_managed, database):
    """Creates a Role/Group."""
    r = current_datastore.create_role(
        id=id, name=name, description=description, is_managed=is_managed
    )
    current_datastore.commit()
    return r


@pytest.fixture(scope="module")
def group(database):
    """A single group."""
    r = _create_group(
        id="it-dep",
        name="it-dep",
        description="IT Department",
        is_managed=True,
        database=database,
    )
    return r


@pytest.fixture(scope="module")
def group2(database):
    """A single group."""
    r = _create_group(
        id="hr-dep",
        name="hr-dep",
        description="HR Department",
        is_managed=True,
        database=database,
    )
    return r


@pytest.fixture(scope="module")
def not_managed_group(database):
    """An unmanaged group."""
    r = _create_group(
        id="not-managed-dep",
        name="not-managed-dep",
        description="A group which is not managed",
        is_managed=False,
        database=database,
    )
    return r


@pytest.fixture(scope="module")
def groups(database, group, group2, not_managed_group):
    """Available indexed groups."""
    roles = [group, group2, not_managed_group]

    current_groups_service.indexer.process_bulk_queue()
    current_groups_service.record_cls.index.refresh()
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


@pytest.fixture(scope="module")
def user_notification_enabled(users):
    """User with notfications enabled."""
    return users["notification_enabled"]


@pytest.fixture(scope="module")
def user_notification_disabled(users):
    """User with notfications disabled."""
    return users["notification_disabled"]


@pytest.fixture(scope="module")
def user_admin(users):
    """User with notfications disabled."""
    return users["admin_user"]


@pytest.fixture(scope="function")
def clear_cache():
    """Clear cache after each test in this module.

    Locking is done using cache, therefore the cache must be cleared after each test to make sure that locks from previous tests are cleared.
    """
    current_cache.cache.clear()


@pytest.fixture(scope="module")
def domains_data():
    """Data for domains."""
    return [
        {
            "domain": "cern.ch",
            "tld": "ch",
            "status": 3,
            "flagged": False,
            "flagged_source": "",
            "category": 1,
            "org_id": 1,
        },
        {
            "domain": "inveniosoftware.org",
            "tld": "org",
            "status": 3,
            "flagged": False,
            "flagged_source": "",
            "org_id": 2,
        },
        {
            "domain": "new.org",
            "tld": "org",
            "status": 1,
            "flagged": False,
            "flagged_source": "",
        },
        {
            "domain": "moderated.org",
            "tld": "org",
            "status": 2,
            "flagged": True,
            "flagged_source": "disposable",
            "category": 3,
        },
        {
            "domain": "spammer.com",
            "tld": "com",
            "status": 4,
            "flagged": True,
            "flagged_source": "",
            "category": 4,
        },
    ]


@pytest.fixture(scope="module")
def domaincategories_data():
    """Data for domains."""
    return [
        {"id": 1, "label": "organization"},
        {"id": 2, "label": "company"},
        {"id": 3, "label": "mail-provider"},
        {"id": 4, "label": "spammer"},
    ]


@pytest.fixture(scope="module")
def domainorgs_data():
    """Data for domains."""
    return [
        {
            "id": 1,
            "pid": "https://ror.org/01ggx4157",
            "name": "CERN",
            "json": {"country": "ch"},
        },
        {
            "id": 2,
            "pid": "https://ror.org/01ggx4157::it",
            "name": "IT department",
            "json": {"country": "ch"},
            "parent_id": 1,
        },
    ]


@pytest.fixture(scope="module")
def domains(app, database, domainorgs_data, domaincategories_data, domains_data):
    """Test domains."""
    for d in domaincategories_data:
        database.session.add(DomainCategory(**d))
    for d in domainorgs_data:
        database.session.add(DomainOrg(**d))
    database.session.commit()

    domains = {}
    for d in domains_data:
        database.session.add(Domain(**d))
        domains[d["domain"]] = d
    database.session.commit()

    current_domains_service.rebuild_index(system_identity)
    current_domains_service.indexer.process_bulk_queue()
    current_domains_service.record_cls.index.refresh()
    return domains
