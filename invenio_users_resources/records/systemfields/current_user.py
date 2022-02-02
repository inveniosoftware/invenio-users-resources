# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""System field for checking if the subject is the current user.."""

from flask_security import current_user
from invenio_records_resources.records.systemfields.calculated import CalculatedField


class CurrentUserField(CalculatedField):
    """System field for checking if the subject is the current user."""

    def calculate(self, record):
        """Check if the given record (user aggregate) is the current user."""
        if not current_user or not current_user.is_authenticated:
            return False

        return current_user.id == record.id
