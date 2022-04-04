# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Hard-coded pagination."""

from invenio_records_resources.pagination import Pagination
from invenio_records_resources.services.records.params import ParamInterpreter


class FixedPagination(ParamInterpreter):
    """Fixed pagination."""

    def apply(self, identity, search, params):
        """Evaluate the fixed pagination on the search."""
        options = self.config.pagination_options
        size = params["size"] = options["default_max_results"]
        page = params["page"] = 1
        p = Pagination(
            size,
            page,
            options["default_max_results"],
        )
        return search[p.from_idx : p.to_idx]
