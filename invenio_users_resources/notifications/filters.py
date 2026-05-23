# SPDX-FileCopyrightText: 2023 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""User specific filters for notifications."""

from invenio_notifications.services.filters import RecipientFilter


class UserPreferencesRecipientFilter(RecipientFilter):
    """Recipient filter for notifications being enabled at all."""

    def __call__(self, notification, recipients):
        """Filter recipients."""
        for key in list(recipients.keys()):
            r = recipients[key]
            prefeferences = r.data.get("preferences")
            if not prefeferences:
                continue

            if not (prefeferences.get("notifications", {}).get("enabled", True)):
                del recipients[key]

        return recipients
