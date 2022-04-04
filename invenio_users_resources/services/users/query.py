# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query tree transformer."""

from functools import partial

from flask_babelex import gettext as _
from invenio_records_resources.services.errors import QuerystringValidationError
from luqum.visitor import TreeTransformer


class FieldTransformer(TreeTransformer):
    """Transform from user-friendly field names to internal field names."""

    def __init__(self, mapping, *args, **kwargs):
        """Constructor."""
        self._mapping = mapping
        super().__init__(self, *args, **kwargs)

    @classmethod
    def factory(cls, mapping=None):
        """Create a new field transformer."""
        return partial(cls, mapping or {})

    def visit_search_field(self, node, context):
        """Visit a search field."""
        if node.name not in self._mapping:
            raise QuerystringValidationError(
                _("Invalid search field: {field_name}.").format(field_name=node.name)
            )
        else:
            new_node = node.clone_item()
            new_node.name = self._mapping[node.name]
            new_node.expr = node.expr.clone_item()
            yield new_node
