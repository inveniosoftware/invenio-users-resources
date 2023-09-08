# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-Vocabularies is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users search facets definitions."""

from invenio_i18n import gettext as _
from invenio_records_resources.services.records.facets import TermsFacet

email_domain = TermsFacet(
    field="email.domain",
    label=_("Email domain"),
)

affiliations = TermsFacet(
    field="profile.affiliations.keyword",
    label=_("Affiliations"),
)
