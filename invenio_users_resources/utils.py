# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Utility functions."""

from .proxies import current_groups_service, current_users_service
from .records.api import GroupAggregate, UserAggregate


def reindex_user(user):
    """Reindex the given user."""
    user_agg = UserAggregate.from_user(user)
    current_users_service.indexer.index(user_agg)


def unindex_user(user):
    """Delete the given user from the index."""
    user_agg = UserAggregate.from_user(user)
    current_users_service.indexer.delete(user_agg)


def reindex_group(role):
    """Reindex the given role/group."""
    group_agg = GroupAggregate.from_role(role)
    current_groups_service.indexer.index(group_agg)


def unindex_group(role):
    """Unindex the given role/group."""
    group_agg = GroupAggregate.from_role(role)
    current_groups_service.indexer.delete(group_agg)
