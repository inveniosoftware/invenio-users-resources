# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User specific generators for notifications."""


from invenio_notifications.models import Recipient
from invenio_notifications.services.generators import RecipientGenerator
from invenio_records.dictutils import dict_lookup


class UserRecipient(RecipientGenerator):
    """User recipient generator for a notification."""

    def __init__(self, key):
        """Ctor."""
        self.key = key

    def __call__(self, notification, recipients):
        """Update required recipient information and add backend id."""
        user = dict_lookup(notification.context, self.key)
        recipients[user["id"]] = Recipient(data=user)
        return recipients
