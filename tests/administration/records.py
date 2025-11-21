# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

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
