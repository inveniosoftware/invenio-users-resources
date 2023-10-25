# -*- coding: utf-8 -*-
#
# Copyright (C)      2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Forms for user resources."""

from flask_wtf import FlaskForm
from invenio_i18n import lazy_gettext as _
from wtforms import BooleanField

from invenio_users_resources.models import NotificationPreferencesProxy


class NotificationsForm(FlaskForm):
    """Form for editing user notification preferences."""

    profile_proxy_cls = NotificationPreferencesProxy

    enabled = BooleanField(
        _("Notify me"),
        description=_("Turn on to enable notifications for relevant events."),
    )

    def process(self, formdata=None, obj=None, data=None, extra_filters=None, **kwargs):
        """Build a proxy around the object."""
        if obj is not None:
            obj = self.profile_proxy_cls(obj)
        super().process(
            formdata=formdata, obj=obj, data=data, extra_filters=extra_filters, **kwargs
        )

    def populate_obj(self, user):
        """Populates the obj."""
        user = self.profile_proxy_cls(user)
        super().populate_obj(user)
