# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Users resources generic needs and permissions."""

from invenio_access import action_factory

USER_MANAGEMENT_ACTION_NAME = "administration-moderation"

user_management_action = action_factory(USER_MANAGEMENT_ACTION_NAME)
