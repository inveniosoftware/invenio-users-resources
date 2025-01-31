# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Domains search facets definitions."""

from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.records.facets import TermsFacet

status = TermsFacet(
    field="status_name",
    label=_("Status"),
    value_labels={
        "new": _("New"),
        "moderated": _("Moderated"),
        "verified": _("Verified"),
        "blocked": _("Blocked"),
    },
)


flagged = TermsFacet(
    field="flagged",
    label=_("Flagged"),
    value_labels={
        True: _("Yes"),
        False: _("No"),
    },
)


category = TermsFacet(
    field="category_name",
    label=_("Category"),
)


organisation = TermsFacet(
    field="org_names",
    label=_("Organisation"),
)


tld = TermsFacet(
    field="tld",
    label=_("Top-level domain"),
)
