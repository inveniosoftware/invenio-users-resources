# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Utility functions."""

from elasticsearch.exceptions import ConflictError
from flask import current_app

from .proxies import current_groups_service, current_users_service
from .records.api import GroupAggregate, UserAggregate


def reindex_user(user):
    """Reindex the given user."""
    if current_users_service.record_cls.index.exists():
        try:
            user_agg = UserAggregate.from_user(user)
            current_users_service.indexer.index(user_agg)
        except ConflictError as e:
            current_app.logger.warn(f"Could not reindex user {user.id}: {e}")


def unindex_user(user):
    """Delete the given user from the index."""
    if current_users_service.record_cls.index.exists():
        try:
            user_agg = UserAggregate.from_user(user)
            current_users_service.indexer.delete(user_agg)
        except ConflictError as e:
            current_app.logger.warn(f"Could not unindex user {user.id}: {e}")


def reindex_group(role):
    """Reindex the given role/group."""
    if current_groups_service.record_cls.index.exists():
        try:
            group_agg = GroupAggregate.from_role(role)
            current_groups_service.indexer.index(group_agg)
        except ConflictError as e:
            current_app.logger.warn(f"Could not reindex group {user.id}: {e}")


def unindex_group(role):
    """Unindex the given role/group."""
    if current_groups_service.record_cls.index.exists():
        try:
            group_agg = GroupAggregate.from_role(role)
            current_groups_service.indexer.delete(group_agg)
        except ConflictError as e:
            current_app.logger.warn(f"Could not unindex group {user.id}: {e}")
