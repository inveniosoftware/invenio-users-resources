# SPDX-FileCopyrightText: 2025 Northwestern University.
# SPDX-License-Identifier: MIT

"""Test administration views for records."""

from invenio_administration.views.base import (
    AdminResourceListView,
)


class RecordAdminListView(AdminResourceListView):
    """Configuration for the records list view."""

    name = "records"
    resource_config = "records_resource"


class DraftAdminListView(AdminResourceListView):
    """Configuration for the drafts list view."""

    name = "drafts"
    resource_config = "records_resource"
