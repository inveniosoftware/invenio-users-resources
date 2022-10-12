# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Search dumper for the email field."""


from invenio_records.dumpers import SearchDumperExt


class EmailFieldDumperExt(SearchDumperExt):
    """Search dumper extension for the email field."""

    def __init__(self, field):
        """Constructor."""
        super().__init__()
        self.field = field
        self.hidden_field = f"{field}_hidden"

    def dump(self, record, data):
        """Dump the data."""
        email = data.pop(self.field, None)

        email_visible = record.preferences["email_visibility"]
        if email_visible == "public":
            data[self.field] = email
        else:
            data[self.hidden_field] = email

    def load(self, data, record_cls):
        """Load the data."""
        email = data.pop(self.hidden_field, None)
        data.setdefault(self.field, email)
