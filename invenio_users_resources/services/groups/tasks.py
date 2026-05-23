# SPDX-FileCopyrightText: 2022 CERN.
# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-License-Identifier: MIT

"""Users service tasks."""

from celery import shared_task
from flask import current_app
from invenio_search.engine import search

from ...proxies import current_groups_service
from ...records.api import GroupAggregate


@shared_task(ignore_result=True)
def reindex_groups(group_ids):
    """Reindex the given groups."""
    index = current_groups_service.record_cls.index
    if current_groups_service.indexer.exists(index):
        try:
            current_groups_service.indexer.bulk_index(group_ids)
        except search.exceptions.ConflictError as e:
            current_app.logger.warn(f"Could not bulk-reindex groups: {e}")


@shared_task(ignore_result=True)
def unindex_groups(group_ids):
    """Unindex the given groups."""
    index = current_groups_service.record_cls.index
    if current_groups_service.indexer.exists(index):
        try:
            current_groups_service.indexer.bulk_delete(group_ids)
        except search.exceptions.ConflictError as e:
            current_app.logger.warn(f"Could not bulk-unindex groups: {e}")
