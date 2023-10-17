# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 KTH Royal Institute of Technology
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 European Union.
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users service."""
from datetime import datetime

from flask import current_app
from invenio_accounts.models import User
from invenio_db import db
from invenio_records_resources.resources.errors import PermissionDeniedError
from invenio_records_resources.services import RecordService
from invenio_records_resources.services.uow import (
    RecordCommitOp,
    RecordIndexOp,
    TaskOp,
    unit_of_work,
)
from invenio_search.engine import dsl
from werkzeug.local import LocalProxy

from invenio_users_resources.services.results import AvatarResult
from invenio_users_resources.services.users.tasks import execute_moderation_actions

from ...records.api import UserAggregate
from .lock import ModerationMutex

mod_lock_timeout = LocalProxy(
    lambda: current_app.config.get("USERS_RESOURCES_MODERATION_LOCK_DEFAULT_TIMEOUT")
)


class UsersService(RecordService):
    """Users service."""

    @property
    def user_cls(self):
        """Alias for record_cls."""
        return self.record_cls

    @unit_of_work()
    def create(self, identity, data, raise_errors=True, uow=None):
        """Create a user."""
        self.require_permission(identity, "create")

        # validate data
        data, errors = self.schema.load(
            data,
            context={"identity": identity},
        )

        # create the user with the specified data
        user = self.user_cls.create(data)

        # run components
        self.run_components(
            "create",
            identity,
            data=data,
            user=user,
            errors=errors,
            uow=uow,
        )

        # persist user to DB (indexing is done in the session hooks, see ext)
        uow.register(RecordCommitOp(user))

        return self.result_item(
            self, identity, user, links_tpl=self.links_item_tpl, errors=errors
        )

    def search(self, identity, params=None, search_preference=None, **kwargs):
        """Search for active and confirmed users, matching the querystring."""
        return super().search(
            identity,
            params=params,
            search_preference=search_preference,
            extra_filter=dsl.Q("term", active=True) & dsl.Q("term", confirmed=True),
            **kwargs,
        )

    def search_all(
        self,
        identity,
        params=None,
        search_preference=None,
        extra_filters=None,
        **kwargs,
    ):
        """Search for all users, without restrictions."""
        self.require_permission(identity, "search_all")

        return super().search(
            identity,
            params=params,
            search_preference=search_preference,
            extra_filter=extra_filters,
            **kwargs,
        )

    def read(self, identity, id_):
        """Retrieve a user."""
        # resolve and require permission
        user = UserAggregate.get_record(id_)
        # TODO - email user issue
        if user is None:
            # return 403 even on empty resource due to security implications
            raise PermissionDeniedError()

        self.require_permission(identity, "read", record=user)

        # run components
        for component in self.components:
            if hasattr(component, "read"):
                component.read(identity, user=user)

        return self.result_item(self, identity, user, links_tpl=self.links_item_tpl)

    def read_avatar(self, identity, id_):
        """Get a user's avatar."""
        user = UserAggregate.get_record(id_)
        if user is None:
            # return 403 even on empty resource due to security implications
            raise PermissionDeniedError()
        self.require_permission(identity, "read", record=user)
        return AvatarResult(user)

    def rebuild_index(self, identity, uow=None):
        """Reindex all users managed by this service."""
        users = db.session.query(User.id).yield_per(1000)
        self.indexer.bulk_index([u.id for u in users])
        return True

    @unit_of_work()
    def block(self, identity, id_, uow=None):
        """Blocks a user."""
        user = UserAggregate.get_record(id_)
        if user is None:
            # return 403 even on empty resource due to security implications
            raise PermissionDeniedError()

        self.require_permission(identity, "manage", record=user)

        # Throws if not acquired
        ModerationMutex(id_).acquire()

        UserAggregate.deactivate(id_)
        user.model.blocked_at = datetime.utcnow()
        user.model.verified_at = None

        user.commit()

        uow.register(RecordIndexOp(user, indexer=self.indexer, index_refresh=True))

        # Register a task to execute callback actions asynchronously, after committing the user
        uow.register(
            TaskOp(execute_moderation_actions, user_id=user.id, action="block")
        )
        return True

    @unit_of_work()
    def restore(self, identity, id_, uow=None):
        """Restores a user."""
        user = UserAggregate.get_record(id_)
        if user is None:
            # return 403 even on empty resource due to security implications
            raise PermissionDeniedError()

        self.require_permission(identity, "manage", record=user)

        # Throws if not acquired
        ModerationMutex(id_).acquire()

        UserAggregate.activate(id_)
        user.model.blocked_at = None
        user.model.verified_at = datetime.utcnow()

        user.commit()

        # User is blocked from now on, "after" actions are executed separately.
        uow.register(RecordIndexOp(user, indexer=self.indexer, index_refresh=True))

        # Register a task to execute callback actions asynchronously, after committing the user
        uow.register(
            TaskOp(execute_moderation_actions, user_id=user.id, action="restore")
        )
        return True

    @unit_of_work()
    def approve(self, identity, id_, uow=None):
        """Approves a user."""
        user = UserAggregate.get_record(id_)
        if user is None:
            # return 403 even on empty resource due to security implications
            raise PermissionDeniedError()

        self.require_permission(identity, "manage", record=user)

        # Throws if not acquired
        ModerationMutex(id_).acquire()

        UserAggregate.activate(id_)
        user.model.blocked_at = None
        user.model.verified_at = datetime.utcnow()

        user.commit()

        uow.register(RecordIndexOp(user, indexer=self.indexer, index_refresh=True))

        # Register a task to execute callback actions asynchronously, after committing the user
        uow.register(
            TaskOp(execute_moderation_actions, user_id=user.id, action="approve")
        )
        return True

    @unit_of_work()
    def deactivate(self, identity, id_, uow=None):
        """Deactivates a user."""
        user = UserAggregate.get_record(id_)
        if user is None:
            # return 403 even on empty resource due to security implications
            raise PermissionDeniedError()

        self.require_permission(identity, "manage", record=user)

        # Throws if not acquired
        ModerationMutex(id_).acquire()

        UserAggregate.deactivate(id_)
        user.model.blocked_at = None
        user.model.verified_at = None

        user.commit()

        uow.register(RecordIndexOp(user, indexer=self.indexer, index_refresh=True))
        return True

    def can_impersonate(self, identity, id_):
        """Check permissions if a user can be impersonated."""
        user = UserAggregate.get_record(id_)
        if user is None:
            # return 403 even on empty resource due to security implications
            raise PermissionDeniedError()
        self.require_permission(identity, "impersonate", record=user)
        return user.model.model_obj
