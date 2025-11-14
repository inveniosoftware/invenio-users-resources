# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Groups search facets definitions."""

from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.records.facets import TermsFacet

is_managed = TermsFacet(
    field="is_managed",
    label=_("Management state"),
    value_labels={
        "false": _("Unmanaged"),
        "true": _("Managed"),
    },
)
