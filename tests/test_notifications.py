# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Notification related tests."""

from invenio_users_resources.notifications import (
    UserPreferencesRecipientFilter,
)
from invenio_users_resources.records.api import UserAggregate


# def test_user_recipient_filter(user_pub):
#     """Test user recipient filter for notifications."""
#     preferences_filter = UserPreferencesRecipientFilter

#     u = UserAggregate.from_user(user_pub.user).dumps()

#     user_notifications_enabled = u.copy()
#     user_notifications_enabled["preferences"]["notifications"] = {
#         "enabled": True
#     }
#     user_notifications_disabled = u.copy()
#     user_notifications_disabled["preferences"]["notifications"] = {
#         "enabled": False
#     }

#     recipient_enabled = {
#         "user": user_notifications_enabled,
#         "backends": [],
#     }
#     recipient_disabled = {
#         "user": user_notifications_disabled,
#         "backends": [],
#     }

#     filtered_users = preferences_filter.run(
#         [
#             recipient_disabled,
#             recipient_enabled,
#         ]
#     )

#     assert 1 == len(filtered_users)
#     assert recipient_enabled == filtered_users[0]["user"]
