# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users and user groups permissions."""

from itertools import chain

from invenio_records_permissions import BasePermissionPolicy
from invenio_records_permissions.generators import AnyUser, Disable, \
    Generator, SystemProcess, UserNeed


class IfPublicEmail(Generator):
    """Generator for different permissions based on the visibility settings."""

    def __init__(self, then_, else_):
        self.then_ = then_
        self.else_ = else_

    def _generators(self, record):
        """Get the "then" or "else" generators."""
        visibility = record.access.get("email_visibility", "hidden")
        email_public = visibility == "public"

        return self.then_ if email_public else self.else_

    def needs(self, record=None, **kwargs):
        """Set of Needs granting permission."""
        needs_chain = chain.from_iterable(
            [
                g.needs(record=record, **kwargs)
                for g in self._generators(record)
            ]
        )
        return list(set(needs_chain))

    def excludes(self, record=None, **kwargs):
        """Set of Needs denying permission."""
        needs_chain = chain.from_iterable(
            [
                g.excludes(record=record, **kwargs)
                for g in self._generators(record)
            ]
        )
        return list(set(needs_chain))


class Self(Generator):
    """Requires the users themselves."""

    def needs(self, record=None, **kwargs):
        """Set of Needs granting permission."""
        if record is not None:
            return [UserNeed(record.id)]

        return []


class UsersPermissionPolicy(BasePermissionPolicy):
    """Permission policy for users and user groups."""

    can_create = [SystemProcess()]
    can_read = [AnyUser(), SystemProcess()]
    can_search = [AnyUser(), SystemProcess()]
    can_update = [SystemProcess()]
    can_delete = [SystemProcess()]

    can_read_email = [IfPublicEmail([AnyUser()], [Self()]), SystemProcess()]
    can_read_details = [Self(), SystemProcess()]
