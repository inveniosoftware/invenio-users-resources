# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2026 KTH Royal Institute of Technology.
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 European Union.
# Copyright (C) 2022-2026 CERN.
# Copyright (C) 2024 Ubiquity Press.
# Copyright (C) 2025 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users service."""

import secrets
import string

from flask import current_app
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

    def _load_user_for_groups(self, identity, id_):
        """Load user and check group-management permissions."""
        user = UserAggregate.get_record(id_)
        if user is None:
            raise PermissionDeniedError()

        self._check_permission(identity, "manage_groups", user)

        return user

    def _normalize_role_id(self, role_id):
        """Normalize a role ID from input."""
        return str(role_id).strip()

    def _normalize_role_ids(self, role_ids):
        """Normalize and de-duplicate role IDs while preserving order."""
        normalized_role_ids = []
        for role_id in role_ids:
            normalized = self._normalize_role_id(role_id)
            if normalized and normalized not in normalized_role_ids:
                normalized_role_ids.append(normalized)
        return normalized_role_ids

    def _resolve_group_ids_or_deny(self, user, role_ids):
        """Resolve role IDs/names and hide existence details on failure."""
        try:
            return user.resolve_group_ids(role_ids)
        except ValidationError as exc:
            raise PermissionDeniedError() from exc

    def _resolve_group_id_or_deny(self, user, role_id):
        """Resolve a single role ID/name and hide existence details on failure."""
        return self._resolve_group_ids_or_deny(user, [role_id])[0]

    def _validate_single_role_mutation(self, user, identity, role_id):
        """Normalize and resolve one role identifier."""
        normalized_role_id = self._normalize_role_id(role_id)
        if not normalized_role_id:
            raise ValidationError({"role_id": ["Role ID cannot be empty."]})

        resolved_role_id = self._resolve_group_id_or_deny(user, normalized_role_id)
        return resolved_role_id

    def _validate_bulk_role_mutation(self, user, identity, role_ids):
        """Normalize and resolve many role identifiers."""
        normalized_role_ids = self._normalize_role_ids(role_ids)
        resolved_role_ids = self._resolve_group_ids_or_deny(user, normalized_role_ids)
        return resolved_role_ids

    def _current_group_ids(self, user):
        """Return current assigned role IDs for a user."""
        return {group["id"] for group in user.get_groups()}

    def _log_group_change(
        self, action, identity, user_id, role_id=None, added=None, removed=None
    ):
        """Log group membership mutations for audit/debugging."""
        actor_id = getattr(identity, "id", None)
        if role_id is not None:
            current_app.logger.info(
                "user_roles action=%s actor_id=%s target_user_id=%s role_id=%s",
                action,
                actor_id,
                user_id,
                role_id,
            )
            return

        added_ids = list(added or [])
        removed_ids = list(removed or [])
        current_app.logger.info(
            "user_roles action=%s actor_id=%s target_user_id=%s added=%s removed=%s",
            action,
            actor_id,
            user_id,
            added_ids,
            removed_ids,
        )

    def get_groups(self, identity, id_):
        """List role IDs for a user."""
        user = UserAggregate.get_record(id_)
        if user is None:
            raise PermissionDeniedError()
        actor_id = getattr(identity, "id", None)
        self.require_permission(
            identity, "read_user_groups", record=user, actor_id=actor_id
        )
        groups = user.get_groups()
        return {"groups": groups, "total": len(groups)}

    @unit_of_work()
    def add_group(self, identity, id_, role_id, uow=None):
        """Add a role to a user."""
        user = self._load_user_for_groups(identity, id_)
        resolved_role_id = self._validate_single_role_mutation(user, identity, role_id)

        current_role_ids = self._current_group_ids(user)
        if resolved_role_id in current_role_ids:
            self._log_group_change("add.noop", identity, id_, role_id=resolved_role_id)
            return True

        user.add_group(resolved_role_id)
        uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))
        self._log_group_change("add", identity, id_, role_id=resolved_role_id)
        return True

    @unit_of_work()
    def remove_group(self, identity, id_, role_id, uow=None):
        """Remove a role from a user."""
        user = self._load_user_for_groups(identity, id_)
        resolved_role_id = self._validate_single_role_mutation(user, identity, role_id)

        current_role_ids = self._current_group_ids(user)
        if resolved_role_id not in current_role_ids:
            self._log_group_change(
                "remove.noop", identity, id_, role_id=resolved_role_id
            )
            return True

        user.remove_group(resolved_role_id)
        uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))
        self._log_group_change("remove", identity, id_, role_id=resolved_role_id)
        return True

    @unit_of_work()
    def set_groups(self, identity, id_, role_ids, uow=None):
        """Replace mutable role memberships for a user."""
        user = self._load_user_for_groups(identity, id_)

        requested_role_ids = self._validate_bulk_role_mutation(user, identity, role_ids)
        current_groups = user.get_groups()
        current_role_ids = [group["id"] for group in current_groups]

        requested = set(requested_role_ids)
        current = set(current_role_ids)
        # Deterministic ordering for both change lists.
        to_add = sorted(requested - current)
        to_remove = sorted(current - requested)

        user.add_groups(to_add)
        user.remove_groups(to_remove)

        if to_add or to_remove:
            uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))
            self._log_group_change(
                "set", identity, id_, added=to_add, removed=to_remove
            )
        else:
            self._log_group_change("set.noop", identity, id_)
        return {
            "added": to_add,
            "removed": to_remove,
            "groups": [group["id"] for group in user.get_groups()],
        }

    @unit_of_work()
    def add_groups(self, identity, id_, role_ids, uow=None):
        """Add multiple role memberships for a user without removing existing."""
        user = self._load_user_for_groups(identity, id_)

        requested_role_ids = self._validate_bulk_role_mutation(user, identity, role_ids)
        requested = set(requested_role_ids)

        current_role_ids = self._current_group_ids(user)
        to_add = sorted(requested - current_role_ids)

        user.add_groups(to_add)

        if to_add:
            uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))
            self._log_group_change("add.bulk", identity, id_, added=to_add)
        else:
            self._log_group_change("add.bulk.noop", identity, id_)

        return {
            "added": to_add,
            "removed": [],
            "groups": [group["id"] for group in user.get_groups()],
        }

    @unit_of_work()
    def remove_groups(self, identity, id_, role_ids, uow=None):
        """Remove multiple role memberships for a user."""
        user = self._load_user_for_groups(identity, id_)

        requested_role_ids = self._validate_bulk_role_mutation(user, identity, role_ids)
        requested = set(requested_role_ids)

        current_role_ids = self._current_group_ids(user)
        to_remove = sorted(requested.intersection(current_role_ids))

        user.remove_groups(to_remove)

        if to_remove:
            uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))
            self._log_group_change("remove.bulk", identity, id_, removed=to_remove)
        else:
            self._log_group_change("remove.bulk.noop", identity, id_)

        return {
            "added": [],
            "removed": to_remove,
            "groups": [group["id"] for group in user.get_groups()],
        }

    @unit_of_work()
    def block(self, identity, id_, uow=None, data=None):
        """Block a user and schedule the registered moderation callbacks.

        The user is marked as blocked synchronously; the follow-up actions
        registered under the ``block`` moderation action (e.g. tombstoning
        the user's records and communities) are executed asynchronously via
        :func:`execute_moderation_actions`.

        :param identity: Identity of the user performing the block; its id
            is forwarded to the callbacks as ``actor_id`` so they can
            attribute the action (e.g. on a tombstone's ``removed_by``).
        :param id_: Id of the user to block.
        :param uow: The unit of work to register the record operations.
            Defaults to None.
        :param data: Free-form dict of caller-supplied context (typically
            the body of the REST request) forwarded verbatim to every
            moderation callback. The semantics of individual fields (for
            example ``removal_reason_id``, ``note``) are defined by the
            callbacks themselves, not by this service. Defaults to None.
        """
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
            TaskOp(
                execute_moderation_actions,
                user_id=user.id,
                action="block",
                actor_id=identity.id,
                data=data or {},
            )
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
