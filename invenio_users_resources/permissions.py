# SPDX-FileCopyrightText: 2023 CERN.
# SPDX-License-Identifier: MIT
"""Users resources generic needs and permissions."""

from invenio_access import action_factory

USER_MANAGEMENT_ACTION_NAME = "administration-moderation"

user_management_action = action_factory(USER_MANAGEMENT_ACTION_NAME)
