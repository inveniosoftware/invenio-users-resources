# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User specific generators for notifications."""

import re

from invenio_notifications.models import Recipient
from invenio_notifications.services.generators import (
    ConditionalRecipientGenerator,
    RecipientGenerator,
)
from invenio_records.dictutils import dict_lookup

# NOTE: this is the python regex from https://emailregex.com/
EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


def _is_email(entity):
    return isinstance(entity, str) and EMAIL_REGEX.fullmatch(entity)


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


class EmailRecipient(RecipientGenerator):
    """Email recipient generator for a notification."""

    def __init__(self, key):
        """Ctor."""
        self.key = key

    def __call__(self, notification, recipients):
        """Add email as recipient."""
        email = dict_lookup(notification.context, self.key)
        recipients[email] = Recipient(data={"email": email})
        return recipients


class IfEmailRecipient(ConditionalRecipientGenerator):
    """Conditional recipient generator checking if entity is email."""

    def __init__(self, key, then_, else_):
        """Ctor."""
        self.key = key
        super().__init__(then_, else_)

    def _condition(self, notification, recipients):
        # Copied from EmailResolver in invenio-rdm-records
        # TODO: Move EmailResolver to invenio-users-resources? Could be reusable.
        entity = dict_lookup(notification.context, self.key)
        return _is_email(entity)


class IfUserRecipient(ConditionalRecipientGenerator):
    """Conditional recipient generator checking if entity is user."""

    def __init__(self, key, then_, else_):
        """Ctor."""
        self.key = key
        super().__init__(then_, else_)

    def _condition(self, notification, recipients):
        entity = dict_lookup(notification.context, self.key)
        if not isinstance(entity, dict):
            return False

        # unresolved check
        return "user" in entity
