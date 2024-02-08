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
from unittest.mock import MagicMock

import pytest
from invenio_access.permissions import system_identity
from marshmallow import ValidationError

from invenio_users_resources.proxies import current_actions_registry
from invenio_users_resources.services.users.lock import ModerationMutex


@pytest.fixture()
def unblocked(user_service, user_res):
    try:
        user_service.activate(system_identity, user_res.id)
    except ValidationError:
        pass


def test_moderation_callbacks_success(
    user_service, user_res, user_moderator, monkeypatch, unblocked, clear_cache
):
    """Test moderation actions (post block / restore)."""
    mocked_method = MagicMock(return_value=True)
    monkeypatch.setitem(current_actions_registry, "block", [mocked_method])
    blocked = user_service.block(user_moderator.identity, user_res.id)
    assert blocked

    # Verify that the callback was called once
    mocked_method.assert_called_once()


def test_moderation_callbacks_failure(
    user_service, user_res, user_moderator, monkeypatch, unblocked, clear_cache
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
    app, user_service, user_res, user_moderator, monkeypatch, unblocked, clear_cache
):
    """Tests the 'simplest' flow for user moderation in terms of locks (e.g. mutex).

    This test validates the basic flow of user moderation in terms of locks. The scenario involves the following steps:

        1. A user is blocked by a moderator.
        2. An action is executed after blocking the user (nothing happens).
        3. The test checks that the user's lock is removed by the celery task, indicating successful moderation.
        4. The test verifies that the user's data is consistent (user is approved and not blocked).
    """

    mocked_method = MagicMock(return_value=True)
    monkeypatch.setitem(
        current_actions_registry,
        "block",
        [mocked_method],
    )

    blocked = user_service.block(user_moderator.identity, user_res.id)
    assert blocked

    # Verify the callback was called. After this, the lock should be released.
    mocked_method.assert_called_once()

    # If the lock does not exist, it was removed by the celery task
    lock = ModerationMutex(user_res.id)
    assert not lock.exists()


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
    clear_cache,
    unblocked,
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

        lock = ModerationMutex(user_id)
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
