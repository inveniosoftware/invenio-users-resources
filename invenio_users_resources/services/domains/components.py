# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Domains service component."""

from invenio_accounts.models import DomainOrg
from invenio_db import db
from invenio_records_resources.services.records.components import ServiceComponent


class DomainComponent(ServiceComponent):
    """Service component for metadata."""

    def create(self, identity, data=None, record=None, errors=None, **kwargs):
        """Inject fields into the record."""
        # Note, DB model takes care of setting tld
        record.domain = data["domain"]
        record.status = data["status"]
        # Optional values
        record.flagged = data.get("flagged", False)
        record.flagged_source = data.get("flagged_source", "")
        record.category = data.get("category", None)
        self._handle_org(data, record)

    def update(self, identity, data=None, record=None, **kwargs):
        """Inject update fields into the domain."""
        # Main part of the validation happens in the schema hence here we just
        # pass on already validated properties.

        # Required values
        record.status = data["status"]
        # Optional values
        record.flagged = data.get("flagged", record.flagged)
        record.flagged_source = data.get("flagged_source", record.flagged_source)
        record.category = data.get("category", record.category)
        self._handle_org(data, record)

    def _handle_org(self, data, record):
        # Handle organisation
        if "org" in data:
            if data["org"] is None:
                record.org_id = None
            else:
                org = data["org"]
                obj = (
                    db.session.query(DomainOrg).filter_by(pid=org["pid"]).one_or_none()
                )
                if obj is None:
                    with db.session.begin_nested():
                        obj = DomainOrg.create(
                            org["pid"], org["name"], json=org.get("props", None)
                        )
                record.org_id = obj.id
