# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users errors."""

from invenio_i18n import lazy_gettext as _


class UsersException(Exception):
    """Base exception for Users errors."""


class UserNotFoundError(UsersException):
    """Exception raised when the user is not found."""

    description = _("The user does not exist.")
