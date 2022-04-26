# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio module providing management APIs for users and roles/groups."""

from invenio_accounts.proxies import current_db_change_history
from invenio_accounts.signals import datastore_post_commit, datastore_pre_commit
from invenio_db import db
from sqlalchemy import event

from . import config
from .records.hooks import post_commit, pre_commit
from .resources import (
    GroupsResource,
    GroupsResourceConfig,
    UsersResource,
    UsersResourceConfig,
)
from .services import (
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
        app.extensions["invenio-users-resources"] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("USERS_RESOURCES_"):
                app.config.setdefault(k, getattr(config, k))

    def init_services(self, app):
        """Initialize the services for users and user groups."""
        self.users_service = UsersService(config=UsersServiceConfig)
        self.groups_service = GroupsService(config=GroupsServiceConfig)

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
            current_db_change_history._clear_dirty_sets(session)
