# SPDX-FileCopyrightText: 2024 CERN
# SPDX-License-Identifier: MIT

"""Domains resource."""

from flask_resources import HTTPJSONException, create_error_handler
from invenio_i18n import lazy_gettext as _
from invenio_records_resources.resources import RecordResource
from sqlalchemy.exc import IntegrityError


#
# Resource
#
class DomainsResource(RecordResource):
    """Resource for domains."""

    error_handlers = {
        **RecordResource.error_handlers,
        IntegrityError: create_error_handler(
            lambda e: HTTPJSONException(
                code=400,
                description=_("Domain already exists."),
            )
        ),
    }
