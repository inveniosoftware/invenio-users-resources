# SPDX-FileCopyrightText: 2025 CERN.
# SPDX-License-Identifier: MIT

"""Users errors."""

from invenio_i18n import lazy_gettext as _


class UsersException(Exception):
    """Base exception for Users errors."""


class UserNotFoundError(UsersException):
    """Exception raised when the user is not found."""

    description = _("The user does not exist.")
