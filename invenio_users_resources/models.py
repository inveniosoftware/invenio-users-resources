# -*- coding: utf-8 -*-
#
# Copyright (C)      2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Proxy models for user preferences."""


class NotificationPreferencesProxy:
    """Proxy for a user that allows mapping the form to the user object."""

    _notification_preferences = lambda self: self._user.preferences.get(
        "notifications", {}
    )

    def __init__(self, user):
        """."""
        super().__setattr__("_user", user)

    def __getattr__(self, attr):
        """."""
        return self._notification_preferences.get(attr, None)

    def __setattr__(self, attr, value):
        """."""
        self._user.preferences = {
            **self._user.preferences,
            "notifications": {
                **(self._notification_preferences()),
                attr: value,
            },
        }

    def __hasattr__(self, attr):
        """."""
        return attr in self._notification_preferences
