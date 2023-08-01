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
from invenio_records_resources.services.uow import UnitOfWork
from invenio_records_resources.tasks import send_change_notifications
from invenio_search.engine import search

from ...proxies import current_actions_registry, current_users_service
from ...records.api import UserAggregate


@shared_task(ignore_result=True)
def reindex_users(user_ids):
    """Reindex the given user."""
    index = current_users_service.record_cls.index
    if current_users_service.indexer.exists(index):
        try:
            user_agg = {
                user_id: UserAggregate.get_record(user_id) for user_id in user_ids
            }
            current_users_service.indexer.bulk_index(user_ids)

            # trigger reindexing of related records
            send_change_notifications(
                "users",
                [
                    (
                        user_agg[user_id].id,
                        str(user_agg[user_id].id),
                        user_agg[user_id].revision_id,
                    )
                    for user_id in user_ids
                ],
            )
        except search.exceptions.ConflictError as e:
            current_app.logger.warn(f"Could not bulk-reindex users: {e}")


@shared_task(ignore_result=True)
def unindex_users(user_ids):
    """Delete the given user from the index."""
    index = current_users_service.record_cls.index
    if current_users_service.indexer.exists(index):
        try:
            current_users_service.indexer.bulk_delete(user_ids)
        except search.exceptions.ConflictError as e:
            current_app.logger.warn(f"Could not bulk-unindex users: {e}")


@shared_task(ignore_result=True)
def execute_moderation_actions(user_id, action):
    """Execute moderation actions.

    Callbacks share the same UOW to guarantee data consistency.
    If any callback fails, then the error is logged and the UOW rolledback.
    """
    actions = current_actions_registry.get(action, [])

    # Create a uow that is shared by all the callables
    uow = UnitOfWork()
    try:
        for callback in actions:
            callback(user_id, uow=uow)
        # Commit the uow when all the callbacks succeeded
        uow.commit()
    except Exception as e:
        current_app.logger.warn(f"Could not execute action '{action}' for user: {e}")
        # If a callback fails, rollback the whole operation and stop processing more callbacks
        uow.rollback()
