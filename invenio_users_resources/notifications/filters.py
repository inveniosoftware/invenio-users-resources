# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User specific filters for notifications."""

from invenio_notifications.services.filters import RecipientFilter


class UserPreferencesRecipientFilter(RecipientFilter):
    """Recipient filter for notifications being enabled at all."""

    def __call__(self, notification, recipients):
        """Filter recipients."""
        for key in list(recipients.keys()):
            r = recipients[key]
            if not (
                r.data.get("preferences", {})
                .get("notifications", {})
                .get("enabled", False)
            ):
                del recipients[key]

        return recipients
