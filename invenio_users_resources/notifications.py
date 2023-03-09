# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User specific resources for notifications."""


from invenio_records_resources.notifications import RecipientFilter


class UserPreferencesRecipientFilter(RecipientFilter):
    """Recipient filter for notifications being enabled at all."""

    def run(self, recipients, **kwargs):
        """Filter recipients."""
        return [
            r
            for r in recipients
            if r.get("user", {})
            .get("preferences", {})
            .get("notifications", {})
            .get("enabled", False)
        ]
