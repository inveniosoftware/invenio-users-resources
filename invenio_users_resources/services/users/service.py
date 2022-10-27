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

from invenio_accounts.models import User
from invenio_records_resources.resources.errors import PermissionDeniedError
from invenio_records_resources.services import RecordService
from invenio_records_resources.services.uow import RecordCommitOp, unit_of_work
from invenio_search.engine import dsl

from invenio_users_resources.services.results import AvatarResult

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

        # persist user to DB (indexing is done in the session hooks, see ext)
        uow.register(RecordCommitOp(user))

        return self.result_item(
            self, identity, user, links_tpl=self.links_item_tpl, errors=errors
        )

    def search(self, identity, params=None, search_preference=None, **kwargs):
        """Search for records matching the querystring."""
        return super().search(
            identity,
            params=params,
            search_preference=search_preference,
            extra_filter=dsl.Q("term", active=True) & dsl.Q("term", confirmed=True),
            **kwargs,
        )

    def read(self, identity, id_):
        """Retrieve a user."""
        # resolve and require permission
        user = UserAggregate.get_record(id_)
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
        users = User.query.all()
        self.indexer.bulk_index([u.id for u in users])

        return True
