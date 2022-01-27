# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users service."""

from invenio_accounts.proxies import current_datastore
from invenio_records_resources.services import LinksTemplate, RecordService


class UsersService(RecordService):
    """Users service."""

    def read(self, identity, id_):
        """Retrieve a user."""
        # resolve and require permission
        user = current_datastore.get_user(id_)
        if user is None:
            raise LookupError(f"there is no user with id {id_}")

        self.require_permission(identity, "read", user=user)

        # run components
        for component in self.components:
            if hasattr(component, "read"):
                component.read(identity, user=user)

        return self.result_item(self, identity, user)

    def search(self, identity, params=None, es_preference=None, **kwargs):
        """Search for users matching the querystring."""
        self.require_permission(identity, "search")

        # Prepare and execute the search
        params = params or {}

        # TODO
        search_result = current_datastore.user_model.query.all()

        return self.result_list(
            self,
            identity,
            search_result,
            params,
            links_tpl=LinksTemplate(self.config.links_search, context={"args": params}),
            links_item_tpl=self.links_item_tpl,
        )

    def get_avatar(self, identity, id_):
        """Get a user's avatar."""
        # TODO
        return None
