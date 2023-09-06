# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Vocabularies is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Facets parameter interpreter API."""

from functools import partial

from invenio_records_resources.services.records.params import ParamInterpreter
from opensearch_dsl.query import Bool


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
        # TODO: only pop if needed.
        value = params.pop(self.param_name, None)
        if value is not None:
            if self.param_name == "is_blocked" or self.param_name == "is_verified":
                if value is True:
                    search = search.filter(
                    Bool(**{"must": {"exists": {"field": self.field_name}}})
                )
                else:
                    search = search.filter(
                    Bool(**{"must_not": {"exists": {"field": self.field_name}}})
                )
            elif self.param_name == "is_active":
                if value is True:
                    search = search.filter("term", **{self.field_name: True})
                else:
                    search = search.filter("term", **{self.field_name: False})

        return search
