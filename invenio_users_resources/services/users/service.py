# SPDX-FileCopyrightText: 2022-2026 KTH Royal Institute of Technology.
# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-FileCopyrightText: 2022 European Union.
# SPDX-FileCopyrightText: 2022-2026 CERN.
# SPDX-FileCopyrightText: 2024 Ubiquity Press.
# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Users service."""

import secrets
import string

from flask import current_app
from flask_security.utils import hash_password
from invenio_access import Permission, superuser_access
from invenio_access.permissions import system_process
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
from invenio_users_resources.services.schemas import GroupSchema
from invenio_users_resources.services.users.tasks import (
    execute_moderation_actions,
    execute_reset_password_email,
)

from ...records.api import GroupAggregate, UserAggregate
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

    def _get_user_or_deny(self, id_):
        """Load user or deny access when it does not exist."""
        user = UserAggregate.get_record(id_)
        if user is None:
            raise PermissionDeniedError()
        return user

    def _can_manage_superadmin_roles(self, identity):
        """Check if identity can mutate superadmin role memberships."""
        return system_process in identity.provides or Permission(
            superuser_access
        ).allows(identity)

    def _resolve_mutable_group_ids(self, identity, user, group_ids, require=False):
        """Resolve and authorize group IDs for membership mutation."""
        try:
            resolved_group_ids = user.resolve_group_ids(group_ids, require=require)
        except ValidationError as exc:
            if require and not any(str(group_id).strip() for group_id in group_ids):
                raise
            raise PermissionDeniedError() from exc

        return resolved_group_ids

    def _deny_superadmin_group_mutation(self, identity, group_ids):
        """Deny non-superadmins from changing superadmin role memberships."""
        if (
            group_ids
            and not self._can_manage_superadmin_roles(identity)
            and GroupAggregate.superadmin_group_ids().intersection(group_ids)
        ):
            raise PermissionDeniedError()

    def _log_groups_update(self, identity, user, result):
        """Log user group membership updates."""
        current_app.logger.info(
            "User '%s' updated user '%s' groups (added: %s, removed: %s)",
            identity.id,
            user.id,
            result["added"],
            result["removed"],
        )

    def get_groups(self, identity, id_):
        """List group assignments and assignable groups for a user."""
        user = self._get_user_or_deny(id_)
        actor_id = getattr(identity, "id", None)
        self.require_permission(
            identity, "read_user_groups", record=user, actor_id=actor_id
        )

        groups = GroupSchema(many=True, only=("id", "name", "is_managed")).dump(
            user.get_groups()
        )
        can_manage_groups = self.check_permission(
            identity, "manage_groups", record=user, actor_id=actor_id
        )
        excluded_group_ids = (
            None
            if self._can_manage_superadmin_roles(identity)
            else GroupAggregate.superadmin_group_ids()
        )
        return {
            "groups": groups,
            "available_groups": (
                GroupSchema(
                    many=True, only=("id", "name", "description", "is_managed")
                ).dump(GroupAggregate.available_groups(excluded_group_ids))
                if can_manage_groups
                else []
            ),
            "total": len(groups),
        }

    @unit_of_work()
    def add_group(self, identity, id_, group_id, uow=None):
        """Add a group to a user."""
        user = self._get_user_or_deny(id_)
        self._check_permission(identity, "manage_groups", user)

        resolved_group_ids = self._resolve_mutable_group_ids(
            identity, user, [group_id], require=True
        )
        self._deny_superadmin_group_mutation(identity, resolved_group_ids)
        result = user.add_groups(resolved_group_ids)
        self._log_groups_update(identity, user, result)
        if result["added"]:
            db.session.flush()
            uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))
        return result

    @unit_of_work()
    def remove_group(self, identity, id_, group_id, uow=None):
        """Remove a group from a user."""
        user = self._get_user_or_deny(id_)
        self._check_permission(identity, "manage_groups", user)

        resolved_group_ids = self._resolve_mutable_group_ids(
            identity, user, [group_id], require=True
        )
        self._deny_superadmin_group_mutation(identity, resolved_group_ids)
        result = user.remove_groups(resolved_group_ids)
        self._log_groups_update(identity, user, result)
        if result["removed"]:
            db.session.flush()
            uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))
        return result

    @unit_of_work()
    def set_groups(self, identity, id_, group_ids, uow=None):
        """Replace group memberships for a user."""
        user = self._get_user_or_deny(id_)
        self._check_permission(identity, "manage_groups", user)

        resolved_group_ids = self._resolve_mutable_group_ids(identity, user, group_ids)
        self._deny_superadmin_group_mutation(
            identity, set(resolved_group_ids).symmetric_difference(user.group_ids())
        )
        result = user.set_groups(resolved_group_ids)
        self._log_groups_update(identity, user, result)
        if result["added"] or result["removed"]:
            db.session.flush()
            uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))
        return result

    @unit_of_work()
    def add_groups(self, identity, id_, group_ids, uow=None):
        """Add multiple group memberships for a user without removing existing."""
        user = self._get_user_or_deny(id_)
        self._check_permission(identity, "manage_groups", user)

        resolved_group_ids = self._resolve_mutable_group_ids(identity, user, group_ids)
        self._deny_superadmin_group_mutation(identity, resolved_group_ids)
        result = user.add_groups(resolved_group_ids)
        self._log_groups_update(identity, user, result)
        if result["added"]:
            db.session.flush()
            uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))
        return result

    @unit_of_work()
    def remove_groups(self, identity, id_, group_ids, uow=None):
        """Remove multiple group memberships for a user."""
        user = self._get_user_or_deny(id_)
        self._check_permission(identity, "manage_groups", user)

        resolved_group_ids = self._resolve_mutable_group_ids(identity, user, group_ids)
        self._deny_superadmin_group_mutation(identity, resolved_group_ids)
        result = user.remove_groups(resolved_group_ids)
        self._log_groups_update(identity, user, result)
        if result["removed"]:
            db.session.flush()
            uow.register(RecordCommitOp(user, indexer=self.indexer, index_refresh=True))
        return result

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
