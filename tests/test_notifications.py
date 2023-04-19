# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Notification related tests."""

from copy import deepcopy

from invenio_notifications.models import Notification, Recipient

from invenio_users_resources.notifications import UserPreferencesRecipientFilter
from invenio_users_resources.records.api import UserAggregate


def test_user_recipient_filter(user_pub):
    """Test user recipient filter for notifications."""
    preferences_filter = UserPreferencesRecipientFilter()

    u = UserAggregate.from_user(user_pub.user).dumps()

    user_notifications_enabled = deepcopy(u)
    user_notifications_enabled["preferences"]["notifications"] = {"enabled": True}
    user_notifications_disabled = deepcopy(u)
    user_notifications_disabled["preferences"]["notifications"] = {"enabled": False}

    n = Notification(type="", context={})
    recipient_enabled = Recipient(data=user_notifications_enabled)
    recipient_disabled = Recipient(data=user_notifications_disabled)

    filtered_recipients = preferences_filter(
        notification=n,
        recipients={
            user_notifications_disabled["id"]: recipient_disabled,
            user_notifications_enabled["id"]: recipient_enabled,
        },
    )

    assert 1 == len(filtered_recipients)
    assert recipient_enabled == filtered_recipients[user_notifications_enabled["id"]]
