# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

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
