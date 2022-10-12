# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permission generators for users and groups."""

import operator
from functools import reduce
from itertools import chain

from invenio_records_permissions.generators import Generator, UserNeed
from invenio_search.engine import dsl


class IfPublic(Generator):
    """Generator for different permissions based on the visibility settings."""

    def __init__(self, field_name, then_, else_):
        """Constructor."""
        self._field_name = field_name
        self.then_ = then_
        self.else_ = else_

    def _generators(self, record):
        """Get the "then" or "else" generators."""
        if record is None:
            return self.else_

        visibility = record.preferences.get(self._field_name, "restricted")
        is_public = visibility == "public"

        return self.then_ if is_public else self.else_

    def needs(self, record=None, **kwargs):
        """Set of Needs granting permission."""
        needs_chain = chain.from_iterable(
            [g.needs(record=record, **kwargs) for g in self._generators(record)]
        )
        return list(set(needs_chain))

    def excludes(self, record=None, **kwargs):
        """Set of Needs denying permission."""
        needs_chain = chain.from_iterable(
            [g.excludes(record=record, **kwargs) for g in self._generators(record)]
        )
        return list(set(needs_chain))

    def make_query(self, generators, **kwargs):
        """Make a query for one set of generators."""
        queries = [g.query_filter(**kwargs) for g in generators]
        queries = [q for q in queries if q]
        return reduce(operator.or_, queries) if queries else None

    def query_filter(self, **kwargs):
        """Filters for queries."""
        field = f"preferences.{self._field_name}"
        q_public = dsl.Q("match", **{field: "public"})
        q_restricted = dsl.Q("match", **{field: "restricted"})
        then_query = self.make_query(self.then_, **kwargs)
        else_query = self.make_query(self.else_, **kwargs)

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
