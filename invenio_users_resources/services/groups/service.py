# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 European Union.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Groups service."""

from invenio_accounts.models import Role
from invenio_records_resources.services import RecordService

from ...records.api import GroupAggregate
from ..results import AvatarResult


class GroupsService(RecordService):
    """User groups service."""

    def read(self, identity, id_):
        """Retrieve a user group."""
        # resolve and require permission
        group = GroupAggregate.get_record(id_)
        if group is None:
            raise LookupError(f"No group with id '{id_}'.")

        self.require_permission(identity, "read", record=group)

        # run components
        for component in self.components:
            if hasattr(component, "read"):
                component.read(identity, group=group)

        return self.result_item(self, identity, group,
                                links_tpl=self.links_item_tpl)

    def read_avatar(self, identity, name_):
        """Get a groups's avatar."""
        group = GroupAggregate.get_record_by_name(name_)
        self.require_permission(identity, "read", record=group)
        return AvatarResult(group)

    def rebuild_index(self, identity, uow=None):
        """Reindex all user groups managed by this service."""
        for role in Role.query.all():
            role_agg = self.record_cls.from_role(role)
            self.indexer.index(role_agg)

        return True
