# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test administration views for domains."""

from invenio_administration.views.base import (
    AdminResourceDetailView,
)


class DomainsDetailView(AdminResourceDetailView):
    """Domain detail view."""

    name = "domains_details"
    resource_config = "domains_resource"
    url = "/domains/<pid_value>"
