# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Users resources generic needs and permissions."""

from flask_principal import RoleNeed
from invenio_access import action_factory
from invenio_access.permissions import Permission

user_moderation_action = action_factory("user-moderation")
user_moderation_permission = Permission(user_moderation_action)

user_moderator = RoleNeed("user-moderation")
