# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permission generators for users and groups."""


from invenio_records.dictutils import dict_lookup
from invenio_records_permissions.generators import (
    ConditionalGenerator,
    Generator,
    UserNeed,
)
from invenio_search.engine import dsl


class IfPublic(ConditionalGenerator):
    """Generator for different permissions based on the visibility settings."""

    def __init__(self, field_name, then_, else_, **kwargs):
        """Constructor."""
        super().__init__(then_=then_, else_=else_, **kwargs)
        self._field_name = field_name

    def _condition(self, record=None, **kwargs):
        """Condition to choose generators set."""
        if record is None:
            return False

        visibility = record.preferences.get(self._field_name, "restricted")
        is_public = visibility == "public"

        return is_public

    def query_filter(self, **kwargs):
        """Filters for queries."""
        field = f"preferences.{self._field_name}"
        q_public = dsl.Q("match", **{field: "public"})
        q_restricted = dsl.Q("match", **{field: "restricted"})
        then_query = self._make_query(self.then_, **kwargs)
        else_query = self._make_query(self.else_, **kwargs)

        if then_query and else_query:
            return (q_public & then_query) | (q_restricted & else_query)
        elif then_query:
            return q_public & then_query
        elif else_query:
            return q_public | (q_restricted & else_query)
        else:
            return q_public


class IfPublicEmail(IfPublic):
    """Generator checking the 'email_visibility' setting."""

    def __init__(self, then_, else_):
        """Constructor."""
        super().__init__("email_visibility", then_, else_)


class IfPublicUser(IfPublic):
    """Generator checking the 'visibility' setting."""

    def __init__(self, then_, else_):
        """Constructor."""
        super().__init__("visibility", then_, else_)


class Self(Generator):
    """Requires the users themselves."""

    def needs(self, record=None, **kwargs):
        """Set of Needs granting permission."""
        if record is not None:
            return [UserNeed(record.id)]

        return []

    def query_filter(self, identity=None, **kwargs):
        """Filters for the current identity."""
        if identity is not None:
            for need in identity.provides:
                if need.method == "id":
                    return dsl.Q("term", id=need.value)

        return []


class IfGroupNotManaged(ConditionalGenerator):
    """Generator for managed group access."""

    def __init__(self, then_, else_, **kwargs):
        """Constructor."""
        super().__init__(then_=then_, else_=else_, **kwargs)
        self._field_name = "is_managed"

    def _condition(self, record, **kwargs):
        """Condition to choose generators set."""
        if record is None:
            return False

        is_managed = dict_lookup(record, self._field_name)
        return not is_managed

    def query_filter(self, **kwargs):
        """Filters for queries."""
        q_all = dsl.Q("match_all")
        q_not_managed = dsl.Q("match", **{self._field_name: False})
        then_query = self._make_query(self.then_, **kwargs)
        else_query = self._make_query(self.else_, **kwargs)

        identity = kwargs.get("identity", None)

        if identity:
            for need in self.needs(**kwargs):
                if need in identity.provides:
                    return q_all & else_query

        return q_not_managed & then_query
