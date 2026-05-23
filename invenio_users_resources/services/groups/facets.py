# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-FileCopyrightText: 2025 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT

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
