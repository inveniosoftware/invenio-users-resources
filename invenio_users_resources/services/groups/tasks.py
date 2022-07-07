# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users service tasks."""

from celery import shared_task
from flask import current_app
from invenio_search.engine import search

from ...proxies import current_groups_service
from ...records.api import GroupAggregate


@shared_task(ignore_result=True)
def reindex_group(role_id):
    """Reindex the given user."""
    index = current_groups_service.record_cls.index
    if current_groups_service.indexer.exists(index):
        try:
            group_agg = GroupAggregate.get_record(role_id)
            current_groups_service.indexer.index(group_agg)
        except search.exceptions.ConflictError as e:
            current_app.logger.warn(f"Could not reindex group {role_id}: {e}")


@shared_task(ignore_result=True)
def unindex_group(role_id):
    """Unindex the given role/group."""
    index = current_groups_service.record_cls.index
    if current_groups_service.indexer.exists(index):
        try:
            group_agg = GroupAggregate.get_record(role_id)
            current_groups_service.indexer.delete(group_agg)
        except search.exceptions.ConflictError as e:
            current_app.logger.warn(f"Could not unindex group {role_id}: {e}")
