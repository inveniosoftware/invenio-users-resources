# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-users-resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Implements locking for users."""

from flask import current_app
from invenio_cache.lock import CachedMutex
from werkzeug.local import LocalProxy

timeout_default = LocalProxy(
    lambda: current_app.config.get("USERS_RESOURCES_MODERATION_LOCK_DEFAULT_TIMEOUT")
)


class ModerationMutex(CachedMutex):
    """Wrapper of ``CachedMutex`` to be used solely in user moderation.

    This class forces the lock ID prefix and specifies a default timeout when acquiring the lock.
    """

    lock_id_prefix = "user_moderation_lock"

    def __init__(self, user_id):
        """Constructor.

        Creates a lock using the parent constructor, building the lock ID as follows:

            <id_prefix>.<user_id>
        """
        super().__init__(lock_id=f"{self.lock_id_prefix}.{user_id}")

    def acquire(self, timeout=None):
        """Acquires the lock.

        If the timeout is not provided, a default is retrieved from the config USERS_RESOURCES_MODERATION_LOCK_DEFAULT_TIMEOUT
        """
        timeout = timeout or timeout_default
        return super().acquire(timeout=timeout_default)
