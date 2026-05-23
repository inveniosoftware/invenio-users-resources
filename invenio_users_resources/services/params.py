# SPDX-FileCopyrightText: 2022 CERN.
# SPDX-License-Identifier: MIT

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
