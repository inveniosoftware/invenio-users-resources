# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Groups resource errors."""

from invenio_i18n import lazy_gettext as _


class GroupsException(Exception):
    """Base exception for groups resource errors."""


class GroupValidationError(GroupsException):
    """Raised when a group payload fails validation."""

    message = _("A validation error occurred.")

    def __init__(self, errors):
        """Marshmallow validation errors."""
        self.errors = errors or {}
        self.description = self.message
        super().__init__(self.message)
