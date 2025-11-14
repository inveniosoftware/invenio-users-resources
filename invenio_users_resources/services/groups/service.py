# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 KTH Royal Institute of Technology
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 European Union.
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Groups service."""

from flask import current_app
from invenio_accounts.models import Role
from invenio_db import db
from invenio_i18n import gettext as _
from invenio_records_resources.resources.errors import PermissionDeniedError
from invenio_records_resources.services import RecordService
from invenio_records_resources.services.uow import (
    RecordCommitOp,
    RecordIndexDeleteOp,
    unit_of_work,
)
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from ...records.api import GroupAggregate
from ...resources.groups.errors import GroupValidationError
from ..results import AvatarResult


class GroupsService(RecordService):
    """User groups service."""

    @unit_of_work()
    def create(self, identity, data, raise_errors=True, uow=None):
        """Create a new group/role."""
        self.require_permission(identity, "create", record=data)
        try:
            data, errors = self.schema.load(
                data or {},
                context={"identity": identity},
                raise_errors=raise_errors,
            )
        except ValidationError as err:
            raise GroupValidationError(err.messages)

        try:
            group = self.record_cls.create(data)
        except IntegrityError as err:
            db.session.rollback()
            raise GroupValidationError(
                {"name": [_("Role name already used by another group.")]}
            ) from err

        current_app.logger.debug(
            "Group created: '%s' by user %s", group.name, identity.id
        )

        self.run_components(
            "create",
            identity,
            data=data,
            group=group,
            errors=errors,
            uow=uow,
        )

        uow.register(RecordCommitOp(group, indexer=self.indexer, index_refresh=True))
        return self.result_item(
            self, identity, group, errors=errors, links_tpl=self.links_item_tpl
        )

    def read(self, identity, id_):
        """Retrieve a user group."""
        group = GroupAggregate.get_record(id_)
        if group is None:
            raise PermissionDeniedError()
        self.require_permission(identity, "read", record=group)
        for component in self.components:
            if hasattr(component, "read"):
                component.read(identity, group=group)
        return self.result_item(self, identity, group, links_tpl=self.links_item_tpl)

    @unit_of_work()
    def update(self, identity, id_, data, raise_errors=True, uow=None):
        """Update an existing group."""
        group = GroupAggregate.get_record(id_)
        if group is None:
            raise PermissionDeniedError()
        self.require_permission(identity, "update", record=group)

        try:
            data, errors = self.schema.load(
                data or {},
                schema_args={"partial": True},
                context={"identity": identity, "record": group},
                raise_errors=raise_errors,
            )
        except ValidationError as err:
            raise GroupValidationError(err.messages) from err

        try:
            group = group.update(data, id_)
        except IntegrityError as err:
            db.session.rollback()
            raise GroupValidationError(
                {"name": [_("Role name already used by another group.")]}
            ) from err
        current_app.logger.debug(
            "Group updated: '%s' by user %s", group.name, identity.id
        )

        self.run_components(
            "update",
            identity,
            data=data,
            group=group,
            errors=errors,
            uow=uow,
        )

        uow.register(RecordCommitOp(group, indexer=self.indexer, index_refresh=True))
        return self.result_item(
            self,
            identity,
            group,
            errors=errors,
            links_tpl=self.links_item_tpl,
        )

    @unit_of_work()
    def delete(self, identity, id_, uow=None):
        """Delete a group."""
        group = GroupAggregate.get_record(id_)
        if group is None:
            raise PermissionDeniedError()
        self.require_permission(identity, "delete", record=group)

        current_app.logger.debug(
            "Group deleted: '%s' by user %s", group.name, identity.id
        )

        # Delete group using API
        group.delete()

        self.run_components(
            "delete",
            identity,
            group=group,
            uow=uow,
        )

        uow.register(
            RecordIndexDeleteOp(group, indexer=self.indexer, index_refresh=True)
        )

        return True

    def read_avatar(self, identity, id_):
        """Get a groups's avatar."""
        group = GroupAggregate.get_record(id_)
        if group is None:
            # return 403 even on empty resource due to security implications
            raise PermissionDeniedError()
        self.require_permission(identity, "read", record=group)
        return AvatarResult(group)

    def rebuild_index(self, identity, uow=None):
        """Reindex all user groups managed by this service."""
        roles = db.session.query(Role.id).yield_per(1000)

        self.indexer.bulk_index([r.id for r in roles])

        return True
