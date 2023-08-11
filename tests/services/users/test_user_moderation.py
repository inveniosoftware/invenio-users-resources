# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-users-resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Tests for user moderation.

These tests are separate from the service because this module will test collateral behaviours from moderating users. Examples:

- Locking mechanisms (involves user service methods and celery tasks)
"""

import time

import pytest
from invenio_access.permissions import system_identity
from invenio_cache.lock import CachedMutex
from invenio_cache.proxies import current_cache

from invenio_users_resources.proxies import current_actions_registry


@pytest.fixture(scope="function", autouse=True)
def clear_cache():
    """Clear cache after each test in this module.

    Locking is done using cache, therefore the cache must be cleared after each test to make sure that locks from previous tests are cleared.
    """
    current_cache.cache.clear()


def test_moderation_callbacks_success(
    user_service, user_res, user_moderator, monkeypatch
):
    """Test moderation actions (post block / restore)."""

    def _block_action(user_id, uow=None):
        """Action to execute after blocking a user."""
        # This action is not useful at all, is just a way of testing that it is executed when blocking a user
        user_service.approve(system_identity, user_id, uow=uow)

    monkeypatch.setitem(current_actions_registry, "block", [_block_action])
    blocked = user_service.block(user_moderator.identity, user_res.id)
    assert blocked

    # Registered action will approve the user, not block them.
    ur = user_service.read(user_moderator.identity, user_res.id)
    assert ur.data["active"] == True


def test_moderation_callbacks_failure(
    user_service, user_res, user_moderator, monkeypatch
):
    """Test moderation actions (post block).

    This aims to test multiple behaviours:
    - If a callback fails, no changes are committed.
    - Even if a callback fails, the user block is committed.
    """

    def _block_action_success(user_id, uow=None):
        """Action to execute after blocking a user."""
        user_service.approve(system_identity, user_id, uow=uow)

    def _block_action_failure(user_id, uow=None):
        """Action raises an exception."""
        raise Exception("Callback failed")

    monkeypatch.setitem(
        current_actions_registry,
        "block",
        [_block_action_success, _block_action_failure],
    )
    blocked = user_service.block(user_moderator.identity, user_res.id)
    assert blocked

    # Registered callbacks will fail and their result won't be committed.
    ur = user_service.read(user_moderator.identity, user_res.id)
    assert ur.data["active"] == False
    assert "blocked_at" in ur.data


def test_moderation_callbacks_lock(
    app, user_service, user_res, user_moderator, monkeypatch
):
    """Tests the 'simplest' flow for user moderation in terms of locks (e.g. mutex).

    This test validates the basic flow of user moderation in terms of locks. The scenario involves the following steps:

        1. A user is blocked by a moderator.
        2. An action is executed after blocking the user (approved in this case).
        3. The test checks that the user's lock is removed by the celery task, indicating successful moderation.
        4. The test verifies that the user's data is consistent (user is approved and not blocked).
    """

    def _block_action_success(user_id, uow=None):
        """Action to execute after blocking a user."""
        user_service.approve(system_identity, user_id, uow=uow)

    monkeypatch.setitem(
        current_actions_registry,
        "block",
        [_block_action_success],
    )

    blocked = user_service.block(user_moderator.identity, user_res.id)
    assert blocked

    # If the lock does not exist, it was removed by the celery task
    lock_prefix = app.config["USERS_RESOURCES_MODERATION_LOCK_KEY_PREFIX"]
    lock_id = f"{lock_prefix}.{user_res.id}"
    lock = CachedMutex(lock_id)
    assert not lock.exists()

    # The after action was executed
    ur = user_service.read(user_moderator.identity, user_res.id)
    assert ur.data["active"] == True
    assert "blocked_at" not in ur.data


@pytest.mark.parametrize(
    "default_timeout, renewal_timeout, expected_lock_state",
    [(1, 10, True), (2, 2, False)],
)
def test_moderation_callbacks_lock_renewal(
    app,
    user_service,
    user_res,
    user_moderator,
    monkeypatch,
    default_timeout,
    renewal_timeout,
    expected_lock_state,
):
    """Tests whether the lock is renewed after moderating a user.

    The test scenario involves the following steps:
        1. A user is moderated, and a lock is created for a specific `default_timeout` period.
        2. A celery task runs, renewing the lock timeout for a `renewal_timeout` period.
        3. The action inside the celery task simulates a process that takes time (sleeps for `default_timeout` seconds).
        4. The test validates whether the lock state matches the expected state after the renewal.


    An example with numbers:

        1) lock is created for 1 second.
        2) lock is renewed for 10 seconds.
        3) task sleeps for 1 second.
        4) if the lock exists, then it was renewed for 10 seconds.
    """

    def _block_action_success(user_id, uow=None):
        """Action to execute after blocking a user."""
        time.sleep(default_timeout)

        lock_prefix = app.config["USERS_RESOURCES_MODERATION_LOCK_KEY_PREFIX"]
        lock_id = f"{lock_prefix}.{user_res.id}"
        lock = CachedMutex(lock_id)
        assert lock.exists() == expected_lock_state

    monkeypatch.setitem(
        current_actions_registry,
        "block",
        [_block_action_success],
    )

    monkeypatch.setitem(
        app.config,
        "USERS_RESOURCES_MODERATION_LOCK_DEFAULT_TIMEOUT",
        default_timeout,
    )
    monkeypatch.setitem(
        app.config,
        "USERS_RESOURCES_MODERATION_LOCK_RENEWAL_TIMEOUT",
        renewal_timeout,
    )
    blocked = user_service.block(user_moderator.identity, user_res.id)
    assert blocked
