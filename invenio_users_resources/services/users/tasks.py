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
from invenio_records_resources.tasks import send_change_notifications
from invenio_search.engine import search

from ...proxies import current_users_service
from ...records.api import UserAggregate


@shared_task(ignore_result=True)
def reindex_user(user_id):
    """Reindex the given user."""
    index = current_users_service.record_cls.index
    if current_users_service.indexer.exists(index):
        try:
            user_agg = UserAggregate.get_record(user_id)
            current_users_service.indexer.index(user_agg)
            # trigger reindexing of related records
            send_change_notifications(
                "users", [(user_agg.id, str(user_agg.id), user_agg.revision_id)]
            )
        except search.exceptions.ConflictError as e:
            current_app.logger.warn(f"Could not reindex user {user_id}: {e}")


@shared_task(ignore_result=True)
def unindex_user(user_id):
    """Delete the given user from the index."""
    index = current_users_service.record_cls.index
    if current_users_service.indexer.exists(index):
        try:
            user_agg = UserAggregate.get_record(user_id)
            current_users_service.indexer.delete(user_agg)
        except search.exceptions.ConflictError as e:
            current_app.logger.warn(f"Could not unindex user {user_id}: {e}")
