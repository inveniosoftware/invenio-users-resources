# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-FileCopyrightText: 2025 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT

"""Groups resource errors."""

from invenio_i18n import lazy_gettext as _


class GroupsException(Exception):
    """Base exception for groups resource errors."""


class GroupValidationError(GroupsException):
    """Raised when a group payload fails validation."""

    message = _("A validation error occurred.")

    def __init__(self, errors):
        """Marshmallow validation errors."""
        self.errors = errors
        self.description = self.message
        super().__init__(self.message)
