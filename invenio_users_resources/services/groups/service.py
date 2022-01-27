# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User groups service."""

from invenio_accounts.proxies import current_datastore
from invenio_records_resources.services import LinksTemplate, RecordService


class UserGroupsService(RecordService):
    """User groups service."""

    def read(self, identity, id_):
        """Retrieve a user group."""
        # resolve and require permission
        role = current_datastore.role_model.query.get(id_)
        if role is None:
            raise LookupError(f"No group with id '{id_}'.")

        self.require_permission(identity, "read", role=role)

        # run components
        for component in self.components:
            if hasattr(component, "read"):
                component.read(identity, role=role)

        return self.result_item(self, identity, role, links_tpl=self.links_item_tpl)

    def search(self, identity, params=None, es_preference=None, **kwargs):
        """Search for users matching the querystring."""
        self.require_permission(identity, "search")

        # Prepare and execute the search
        params = params or {}

        # TODO
        search_result = current_datastore.role_model.query.all()

        return self.result_list(
            self,
            identity,
            search_result,
            params,
            links_tpl=LinksTemplate(self.config.links_search, context={"args": params}),
            links_item_tpl=self.links_item_tpl,
        )

    def get_avatar(self, identity, id_):
        """Get a user group's avatar."""
        # TODO
        print("getting that group avatar")
        return None
