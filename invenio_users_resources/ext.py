# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio module providing management APIs for users and roles/groups."""

from collections import defaultdict

from invenio_accounts.models import Role, User
from invenio_db import db
from invenio_userprofiles.models import UserProfile
from sqlalchemy import event

from . import config
from .resources import GroupsResource, GroupsResourceConfig, UsersResource, \
    UsersResourceConfig
from .services import GroupsService, GroupsServiceConfig, UsersService, \
    UsersServiceConfig
from .utils import reindex_group, reindex_user, unindex_group, unindex_user


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
        self.init_db_hooks(app)
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

    def init_db_hooks(self, app):
        """Initialize the database hooks for reindexing updated users/roles."""
        # make sure that the hooks are only registered once per DB connection
        # and not once per app
        if hasattr(db, "_user_resources_hooks_registered"):
            return
        db._user_resources_hooks_registered = True

        # the keys are going to be the sessions, the values are going to be
        # the sets of dirty/deleted models
        updated_users = defaultdict(lambda: list())
        updated_roles = defaultdict(lambda: list())
        deleted_users = defaultdict(lambda: list())
        deleted_roles = defaultdict(lambda: list())

        def _clear_dirty_sets(session):
            """Clear the dirty sets for the given session."""
            sid = id(session)
            updated_users.pop(sid, None)
            updated_roles.pop(sid, None)
            deleted_users.pop(sid, None)
            deleted_roles.pop(sid, None)

        @event.listens_for(db.session, "before_commit")
        def _before_commit(session):
            """Find out which entities need indexing before commit."""
            # it seems that the {dirty,new,deleted} sets aren't populated
            # in after_commit anymore, that's why we need to collect the
            # information here
            updated = set(session.dirty).union(set(session.new))
            deleted = set(session.deleted)
            sid = id(session)

            try:
                # session._model_changes is a dictionary that contains
                # references to all entities changed in the transaction
                # we use this because it seems like sometimes changes to
                # models aren't listed in session.dirty, but are listed
                # in this collection, especially with UserProfiles
                changes = session._model_changes.values()
                updated = updated.union(
                    {m for (m, op) in changes if op == "update"}
                )
            except Exception as e:
                app.logger.warn(f"Error while checking DB model changes: {e}")

            # flush the session s.t. related models are queryable
            session.flush()

            # users need to be reindexed if their user model was updated, or
            # their profile was changed (or even possibly deleted)
            users1 = {u for u in updated if isinstance(u, User)}
            users2 = {p.user for p in updated if isinstance(p, UserProfile)}
            users3 = {p.user for p in deleted if isinstance(p, UserProfile)}

            updated_users[sid] = list(users1.union(users2).union(users3))
            updated_roles[sid] = [r for r in updated if isinstance(r, Role)]

            deleted_users[sid] = [u for u in deleted if isinstance(u, User)]
            deleted_roles[sid] = [r for r in deleted if isinstance(r, Role)]

            # force loading of user profile before the commit is done
            for user in updated_users[sid]:
                user.profile is None  # noqa

        @event.listens_for(db.session, "after_commit")
        def _after_commit(session):
            """Reindex all modified users and roles after the DB commit."""
            # since this function is called after the commit, no more
            # DB operations are allowed here, not even lazy-loading of
            # properties!
            sid = id(session)
            for user in updated_users[sid]:
                reindex_user(user)
            for role in updated_roles[sid]:
                reindex_group(role)

            for user in deleted_users[sid]:
                unindex_user(user)
            for role in deleted_roles[sid]:
                unindex_group(role)

            _clear_dirty_sets(session)

        @event.listens_for(db.session, "after_rollback")
        def _after_rollback(session):
            """When a session is rolled back, we don't reindex anything."""
            _clear_dirty_sets(session)
