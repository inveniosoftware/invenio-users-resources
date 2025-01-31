# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-Vocabularies is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users search facets definitions."""

from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.records.facets import TermsFacet

domain = TermsFacet(
    field="domain",
    label=_("Domain"),
)

domain_status = TermsFacet(
    field="domaininfo.status",
    label=_("Domain status"),
    value_labels={
        1: _("New"),
        2: _("Moderated"),
        3: _("Verified"),
        4: _("Blocked"),
    },
)

affiliations = TermsFacet(
    field="profile.affiliations.keyword",
    label=_("Affiliations"),
)

status = TermsFacet(
    field="status",
    label=_("Account status"),
    value_labels={
        "new": _("New"),
        "verified": _("Verified"),
        "confirmed": _("Confirmed"),
        "blocked": _("Blocked"),
        "inactive": _("Inactive"),
    },
)

visibility = TermsFacet(
    field="visibility",
    label=_("Profile visibility"),
    value_labels={
        "hidden": _("Hidden"),
        "profile": _("Profile"),
        "full": _("Full"),
    },
)
