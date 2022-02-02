# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users service."""

from invenio_accounts.models import User
from invenio_records_resources.services import RecordService
from invenio_records_resources.services.uow import RecordCommitOp, unit_of_work

from ...records.api import UserAggregate


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

        # persist user (DB and index)
        uow.register(RecordCommitOp(user, self.indexer))

        return self.result_item(
            self, identity, user, links_tpl=self.links_item_tpl, errors=errors
        )

    def read(self, identity, id_):
        """Retrieve a user."""
        # resolve and require permission
        user = UserAggregate.get_record(id_)
        if user is None:
            raise LookupError(f"No user with id '{id_}'.")

        self.require_permission(identity, "read", record=user)

        # run components
        for component in self.components:
            if hasattr(component, "read"):
                component.read(identity, user=user)

        return self.result_item(
            self, identity, user, links_tpl=self.links_item_tpl
        )

    def get_avatar(self, identity, id_):
        """Get a user's avatar."""
        # TODO
        return None

    def rebuild_index(self, identity, uow=None):
        """Reindex all users managed by this service."""
        for user in User.query.all():
            user_agg = self.record_cls.from_user(user)
            self.indexer.index(user_agg)

        return True
