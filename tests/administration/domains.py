# SPDX-FileCopyrightText: 2025 Northwestern University.
# SPDX-License-Identifier: MIT

"""Test administration views for domains."""

from invenio_administration.views.base import (
    AdminResourceDetailView,
)


class DomainsDetailView(AdminResourceDetailView):
    """Domain detail view."""

    name = "domains_details"
    resource_config = "domains_resource"
    url = "/domains/<pid_value>"
