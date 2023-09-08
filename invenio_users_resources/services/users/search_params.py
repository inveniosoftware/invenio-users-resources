# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-Vocabularies is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Filter parameter interpreter API."""

from functools import partial

from invenio_records_resources.services.records.params import ParamInterpreter
from invenio_search.engine import dsl


class ModerationFilterParam(ParamInterpreter):
    """Evaluate type filter."""

    def __init__(self, param_name, field_name, config):
        """."""
        self.param_name = param_name
        self.field_name = field_name
        super().__init__(config)

    @classmethod
    def factory(cls, param=None, field=None):
        """Create a new filter parameter."""
        return partial(cls, param, field)

    def apply(self, identity, search, params):
        """Applies a filter to get only records for a specific type."""
        # Pop because we don't want it to show up in links.
        value = params.pop(self.param_name, None)
        # TODO this can be broken down to separate param components
        if value is not None:
            if self.param_name == "is_blocked" or self.param_name == "is_verified":
                if value is True:
                    search = search.filter(
                        dsl.query.Bool(
                            **{"must": {"exists": {"field": self.field_name}}}
                        )
                    )
                else:
                    search = search.filter(
                        dsl.query.Bool(
                            **{"must_not": {"exists": {"field": self.field_name}}}
                        )
                    )
            elif self.param_name == "is_active":
                if value is True:
                    search = search.filter("term", **{self.field_name: True})
                else:
                    # search only active but not blocked
                    search = search.filter(
                        dsl.query.Q("term", **{self.field_name: False})
                        & dsl.query.Bool(
                            **{"must_not": {"exists": {"field": "blocked_at"}}}
                        )
                    )

        return search
