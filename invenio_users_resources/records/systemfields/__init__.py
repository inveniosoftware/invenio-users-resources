# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Data-layer definitions for user and group management in Invenio."""

from invenio_accounts.models import DomainOrg, UserIdentity
from invenio_accounts.proxies import current_datastore
from invenio_accounts.utils import DomainStatus
from invenio_db import db
from invenio_records_resources.records.systemfields.calculated import CalculatedField


class CalculatedIndexedField(CalculatedField):
    """Field that also indexes it's calculated value."""

    def __init__(self, key=None, use_cache=False, index=False):
        """Constructor."""
        super().__init__(key, use_cache=use_cache)
        self._index = index

    def pre_dump(self, record, data, dumper=None):
        """Called after a record is dumped."""
        if self._index:
            data[self.attr_name] = self.obj(record)

    def post_load(self, record, data, loader=None):
        """Called after a record is loaded."""
        if self._index:
            value = data.pop(self.attr_name, None)
            # Store on cache so if cache is used we don't fetch the object again.
            self._set_cache(record, value)


class AccountStatusField(CalculatedIndexedField):
    """Dump a combined account status value."""

    def calculate(self, user_record):
        """Logic for calculating the record's property."""
        status = "new"
        if user_record.active:
            if user_record.confirmed_at and user_record.verified_at:
                status = "verified"
            elif user_record.confirmed_at:
                status = "confirmed"
        else:
            if user_record.blocked_at:
                status = "blocked"
            else:
                status = "inactive"
        return status


class AccountVisibilityField(CalculatedIndexedField):
    """Dump a combined visibility status value."""

    def calculate(self, user_record):
        """Logic for calculating visibility status."""
        if user_record.preferences["email_visibility"] == "public":
            return "full"
        elif user_record.preferences["visibility"] == "public":
            return "profile"
        else:
            return "hidden"


class IsNotNoneField(CalculatedIndexedField):
    """Dump a bool for easier checking if a value is set."""

    def __init__(self, field, *args, **kwargs):
        """Constructor."""
        self._field = field
        super().__init__(*args, **kwargs)

    def calculate(self, user_record):
        """Checks if a timestamp is not none."""
        return getattr(user_record, self._field, None) is not None


class DomainField(CalculatedIndexedField):
    """Get information about the user's domain."""

    def calculate(self, user_record):
        """Checks if a timestamp is not none."""
        domain = current_datastore.find_domain(user_record.domain)
        if domain is None:
            return {
                "tld": "",
                "status": "1",
                "category": None,
                "flagged": False,
            }
        else:
            return {
                "tld": domain.tld,
                "status": domain.status.value,
                "category": domain.category,
                "flagged": domain.flagged,
            }


class UserIdentitiesField(CalculatedIndexedField):
    """Get a user's different linked account identities."""

    def calculate(self, user_record):
        """Checks if a timestamp is not none."""
        identities = (
            db.session.query(UserIdentity).filter_by(id_user=user_record.id).all()
        )
        data = {i.method: i.id for i in identities}
        return data


class DomainOrgField(CalculatedIndexedField):
    """Get information about the user's domain."""

    def calculate(self, domain_record):
        """Checks if a timestamp is not none."""
        if not domain_record.model.org_id:
            return None

        org = domain_record.model.model_obj.org

        parent_org = None
        if org.parent_id is not None:
            parent_org = org.parent

        data = [
            {
                "id": org.id,
                "pid": org.pid,
                "name": org.name,
                "props": org.json or {},
                "is_parent": False,
            }
        ]
        if parent_org:
            data.append(
                {
                    "id": parent_org.id,
                    "pid": parent_org.pid,
                    "name": parent_org.name,
                    "props": parent_org.json or {},
                    "is_parent": True,
                }
            )
        return data


class DomainCategoryNameField(CalculatedIndexedField):
    """Dump the name of the category."""

    def calculate(self, domain_record):
        """Logic for calculating."""
        if domain_record.model.model_obj.category:
            return domain_record.model.model_obj.category_name.label
        else:
            return None


class DomainStatusNameField(CalculatedIndexedField):
    """Dump the name of the category."""

    def calculate(self, domain_record):
        """Logic for calculating."""
        return DomainStatus(domain_record.status).name
