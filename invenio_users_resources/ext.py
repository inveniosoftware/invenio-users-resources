# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2023-2024 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio module providing management APIs for users and roles/groups."""

from invenio_accounts.proxies import current_db_change_history
from invenio_accounts.signals import datastore_post_commit, datastore_pre_commit
from invenio_base.utils import entry_points
from invenio_db import db
from sqlalchemy import event

from . import config
from .records.hooks import post_commit, pre_commit
from .resources import (
    DomainsResource,
    DomainsResourceConfig,
    GroupsResource,
    GroupsResourceConfig,
    UsersResource,
    UsersResourceConfig,
)
from .services import (
    DomainsService,
    DomainsServiceConfig,
    GroupsService,
    GroupsServiceConfig,
    UsersService,
    UsersServiceConfig,
)


class InvenioUsersResources(object):
    """Invenio-Users-Resources extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.init_services(app)
        self.init_resources(app)
        self.init_db_hooks()
        self.init_actions_registry()
        app.extensions["invenio-users-resources"] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("USERS_RESOURCES_"):
                app.config.setdefault(k, getattr(config, k))

    def init_services(self, app):
        """Initialize the services for users and user groups."""
        self.users_service = UsersService(config=UsersServiceConfig.build(app))
        self.groups_service = GroupsService(config=GroupsServiceConfig)
        self.domains_service = DomainsService(config=DomainsServiceConfig.build(app))

    def init_resources(self, app):
        """Initialize the resources for users and user groups."""
        self.users_resource = UsersResource(
            service=self.users_service,
            config=UsersResourceConfig,
        )
        self.groups_resource = GroupsResource(
            service=self.groups_service,
            config=GroupsResourceConfig,
        )

        self.domains_resource = DomainsResource(
            service=self.domains_service,
            config=DomainsResourceConfig,
        )

    def init_db_hooks(self):
        """Initialize the database hooks for reindexing updated users/roles."""
        # make sure that the hooks are only registered once per DB connection
        # and not once per app
        if hasattr(db, "_user_resources_hooks_registered"):
            return
        db._user_resources_hooks_registered = True
        datastore_pre_commit.connect(pre_commit)
        datastore_post_commit.connect(post_commit)

        @event.listens_for(db.session, "after_rollback")
        def _after_rollback(session):
            """When a session is rolled back, we don't reindex anything."""
            # this event listener is triggered when the entire transaction is
            # rollbacked. In a case (e.g. nested transactions) when an
            # exception is caught and then the session is commited,
            # the sets might not reflect all the users that were changed.
            current_db_change_history.clear_dirty_sets(session)

    def init_actions_registry(self):
        """Initialises moderation actions registry."""
        self.actions_registry = {}
        self._register_entry_point(
            self.actions_registry,
            "invenio_users_resources.moderation.actions",
        )

    def _register_entry_point(self, registry, ep_name):
        """Load entry points into the given registry."""
        for ep in entry_points(group=ep_name):
            # Entry point has the action as the name (e.g. invenio_users_resources.moderation.actions.block = ... , 'block' is the name)
            action_name = ep.name
            action = ep.load()
            assert callable(action)
            registry.setdefault(action_name, []).append(action)


def finalize_app(app):
    """Finalize app.

    NOTE: replace former @record_once decorator
    """
    init(app)


def api_finalize_app(app):
    """Finalize app for api.

    NOTE: replace former @record_once decorator
    """
    init(app)


def init(app):
    """Init app.

    Register services - cannot be done in extension because
    Invenio-Records-Resources might not have been initialized.
    """
    rr_ext = app.extensions["invenio-records-resources"]
    ext = app.extensions["invenio-users-resources"]
    idx_ext = app.extensions["invenio-indexer"]

    # services
    rr_ext.registry.register(ext.users_service)
    rr_ext.registry.register(ext.groups_service)
    rr_ext.registry.register(ext.domains_service)

    idx_ext.registry.register(ext.users_service.indexer, indexer_id="users")
    idx_ext.registry.register(ext.groups_service.indexer, indexer_id="groups")
    idx_ext.registry.register(ext.domains_service.indexer, indexer_id="domains")
