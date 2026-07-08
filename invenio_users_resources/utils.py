# SPDX-FileCopyrightText: 2026 TU Wien.
# SPDX-License-Identifier: MIT

"""Utilities for Invenio-Users-Resources."""

from werkzeug.routing import BaseConverter, ValidationError


class UserIDConverter(BaseConverter):
    """Flask URL converter for user IDs."""

    def __init__(self, map, special_value=None):
        """Constructor."""
        self.special_value = special_value or "system"

    def to_python(self, value):
        """Accept the special value (e.g. "system") or any positive integer value."""
        try:
            if value == self.special_value:
                return None

            # make sure that we're dealing with a positive integer
            value = int(value)
            if value <= 0:
                raise ValidationError()

            # the marshmallow validation layer expects a string
            return str(value)
        except ValueError as e:
            raise ValidationError() from e

    def to_url(self, value):
        """Turn the user ID into a string."""
        return (
            self.special_value
            if value is None or value == self.special_value
            else str(value)
        )
