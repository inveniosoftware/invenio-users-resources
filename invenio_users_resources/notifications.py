# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User specific resources for notifications."""


from invenio_accounts.models import User
from invenio_notifications.models import Recipient
from invenio_notifications.services.filters import RecipientFilter


class UserPreferencesRecipientFilter(RecipientFilter):
    """Recipient filter for notifications being enabled at all."""

    @classmethod
    def __call___(cls, notification, recipients):
        """Filter recipients."""
        recipients = [
            r
            for r in recipients
            if r.get("data", {})
            .get("preferences", {})
            .get("notifications", {})
            .get("enabled", False)
        ]
        return recipients


class UserRecipient:
    def __init__(self, key):
        """Ctor."""
        self.key = key

    def __call__(self, notification, recipients):
        """Update required recipient information and add backend id."""
        user = notification[self.key]
        if isinstance(user, User):
            if user.preferences["notifications"]["enabled"]:
                recipients[user.id] = Recipient(data=user.dump())
        else:
            recipients[user.get("id")] = Recipient(data=user)
        return recipients


class UserEmailBackend:
    def __call__(self, notification, recipient):
        """Update required recipient information and add backend id."""
        return "email"
        # user = recipient.data
        # rec.backends.append(
        #     {
        #         "backend": "email",
        #         "to": f"{user.profile.full_name} <{user.email}>",
        #     }
        # )
