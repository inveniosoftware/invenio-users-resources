# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2024 KTH Royal Institute of Technology.
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 European Union.
# Copyright (C) 2022 CERN.
# Copyright (C) 2024 Ubiquity Press.
# Copyright (C) 2025 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users service."""

import secrets
import string

from flask_security.utils import hash_password
from invenio_accounts.models import User
from invenio_accounts.proxies import current_datastore
from invenio_accounts.utils import default_reset_password_link_func
from invenio_db import db
from invenio_records_resources.resources.errors import PermissionDeniedError
from invenio_records_resources.services import RecordService
from invenio_records_resources.services.uow import RecordCommitOp, TaskOp, unit_of_work
from invenio_search.engine import dsl
from marshmallow import ValidationError

from invenio_users_resources.services.results import AvatarResult
from invenio_users_resources.services.users.tasks import (
    execute_moderation_actions,
    execute_reset_password_email,
)

from ...records.api import UserAggregate
from .lock import ModerationMutex


class UsersService(RecordService):
    """Users service."""

    @property
    def user_cls(self):
        """Alias for record_cls."""
        return self.record_cls

    @unit_of_work()
    def create(self, identity, data, raise_errors=True, uow=None):
        """Create a user from users admin."""
        self.require_permission(identity, "create")
        # Remove None values to avoid validation issues
        data = {k: v for k, v in data.items() if v is not None}
        # validate new user data
        data, errors = self.schema.load(
            data,
            context={"identity": identity},
            raise_errors=raise_errors,
        )
        # create user
        user = self._create_user(data)
        # run components
        self.run_components(
            "create",
            identity,
            data=data,
            user=user,
            errors=errors,
            uow=uow,
        )
        uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))
        # get email token and reset info
        account_user = current_datastore.get_user_by_id(user.id)
        token, reset_link = default_reset_password_link_func(account_user)
        # trigger celery task to send email after the user was successfully created
        uow.register(
            TaskOp(
                execute_reset_password_email,
                user_id=user.id,
                token=token,
                reset_link=reset_link,
            )
        )
        return self.result_item(
            self, identity, user, links_tpl=self.links_item_tpl, errors=errors
        )

    def _generate_password(self, length=12):
        """Generate password of a specific length."""
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _create_user(self, user_info: dict):
        """Create a new active and verified user with auto-generated password."""
        # Generate password and add to user_info dict
        user_info["password"] = hash_password(self._generate_password())

        # Create the user with the specified data
        user = self.user_cls.create(user_info)
        # Activate and verify user
        user.activate()
        user.verify()
        return user

    def search(self, identity, params=None, search_preference=None, **kwargs):
        """Search for active and confirmed users, matching the query."""
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
            search_opts=self.config.search_all,
            permission_action="read_all",
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

    def _check_permission(self, identity, permission_type, user):
        """Checks if given identity has the specified permission type on the user."""
        self.require_permission(
            identity, permission_type, record=user, actor_id=identity.id
        )

    @unit_of_work()
    def block(self, identity, id_, uow=None):
        """Blocks a user."""
        user = UserAggregate.get_record(id_)
        if user is None:
            # return 403 even on empty resource due to security implications
            raise PermissionDeniedError()
        self._check_permission(identity, "manage", user)

        if user.blocked:
            raise ValidationError("User is already blocked.")

        # Throws if not acquired
        ModerationMutex(id_).acquire()
        user.block()
        uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))

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
        self._check_permission(identity, "manage", user)

        if not user.blocked:
            raise ValidationError("User is not blocked.")

        # Throws if not acquired
        ModerationMutex(id_).acquire()
        user.activate()
        # User is blocked from now on, "after" actions are executed separately.
        uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))

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
        self._check_permission(identity, "manage", user)

        if user.verified:
            raise ValidationError("User is already verified.")

        # Throws if not acquired
        ModerationMutex(id_).acquire()
        user.verify()
        uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))

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
        self._check_permission(identity, "manage", user)

        if not user.active:
            raise ValidationError("User is already inactive.")

        user.deactivate()
        uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))
        return True

    @unit_of_work()
    def activate(self, identity, id_, uow=None):
        """Activate a user."""
        user = UserAggregate.get_record(id_)
        if user is None:
            # return 403 even on empty resource due to security implications
            raise PermissionDeniedError()
        self._check_permission(identity, "manage", user)

        if user.active and user.confirmed:
            raise ValidationError("User is already active.")
        user.activate()
        uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))
        return True

    def can_impersonate(self, identity, id_):
        """Check permissions if a user can be impersonated."""
        user = UserAggregate.get_record(id_)
        if user is None:
            # return 403 even on empty resource due to security implications
            raise PermissionDeniedError()
        self._check_permission(identity, "impersonate", user)

        return user.model.model_obj
