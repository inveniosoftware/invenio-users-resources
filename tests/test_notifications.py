# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Notification related tests."""

from invenio_notifications.models import Notification, Recipient

from invenio_users_resources.notifications.filters import UserPreferencesRecipientFilter
from invenio_users_resources.notifications.generators import UserRecipient
from invenio_users_resources.records.api import UserAggregate
from invenio_users_resources.records.models import UserAggregateModel


def test_user_recipient_generator(
    user_notification_disabled, user_notification_enabled
):
    generator_disabled = UserRecipient(key="disabled")
    generator_enabled = UserRecipient(key="enabled")

    user_notifications_disabled = UserAggregate.from_model(
        user_notification_disabled.user
    ).dumps()
    user_notifications_enabled = UserAggregate.from_model(
        user_notification_enabled.user
    ).dumps()

    n = Notification(
        type="",
        context={
            "disabled": user_notifications_disabled,
            "enabled": user_notifications_enabled,
        },
    )

    recipients = {}

    generator_disabled(n, recipients=recipients)
    assert 1 == len(recipients)
    assert user_notifications_disabled["id"] in recipients.keys()

    generator_enabled(n, recipients=recipients)
    assert 2 == len(recipients)
    assert [
        user_notifications_disabled["id"],
        user_notifications_enabled["id"],
    ] == list(recipients)

    # checking that user does not get added twice
    generator_disabled(n, recipients=recipients)
    assert 2 == len(recipients)
    assert [
        user_notifications_disabled["id"],
        user_notifications_enabled["id"],
    ] == list(recipients)


def test_user_recipient_filter(user_notification_disabled, user_notification_enabled):
    """Test user recipient filter for notifications."""

    user_notifications_disabled = UserAggregate.from_model(
        user_notification_disabled.user
    ).dumps()
    user_notifications_enabled = UserAggregate.from_model(
        user_notification_enabled.user
    ).dumps()

    n = Notification(type="", context={})
    recipient_enabled = Recipient(data=user_notifications_enabled)
    recipient_disabled = Recipient(data=user_notifications_disabled)

    recipients = {
        user_notifications_disabled["id"]: recipient_disabled,
        user_notifications_enabled["id"]: recipient_enabled,
    }

    preferences_filter = UserPreferencesRecipientFilter()
    filtered_recipients = preferences_filter(
        notification=n,
        recipients=recipients,
    )

    assert 1 == len(filtered_recipients)
    assert recipient_enabled == filtered_recipients[user_notifications_enabled["id"]]
