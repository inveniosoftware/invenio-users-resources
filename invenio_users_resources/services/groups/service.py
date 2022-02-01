# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User groups service."""

from invenio_accounts.models import Role
from invenio_accounts.proxies import current_datastore
from invenio_records_resources.services import LinksTemplate, RecordService

from ...records.api import UserGroupAggregate


class UserGroupsService(RecordService):
    """User groups service."""

    def read(self, identity, id_):
        """Retrieve a user group."""
        # resolve and require permission
        group = UserGroupAggregate.get_record(id_)
        if group is None:
            raise LookupError(f"No group with id '{id_}'.")

        self.require_permission(identity, "read", group=group)

        # run components
        for component in self.components:
            if hasattr(component, "read"):
                component.read(identity, group=group)

        return self.result_item(
            self, identity, group, links_tpl=self.links_item_tpl
        )

    def get_avatar(self, identity, id_):
        """Get a user group's avatar."""
        # TODO
        print("getting that group avatar")
        return None

    def rebuild_index(self, identity, uow=None):
        """Reindex all user groups managed by this service."""
        for role in Role.query.all():
            role_agg = self.record_cls.from_role(role)
            self.indexer.index(role_agg)

        return True
