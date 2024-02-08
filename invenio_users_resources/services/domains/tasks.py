# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users service tasks."""

from celery import shared_task
from flask import current_app
from invenio_search.engine import search

from ...proxies import current_domains_service


@shared_task(ignore_result=True)
def reindex_domains(domain_ids):
    """Reindex the given domains."""
    index = current_domains_service.record_cls.index
    if current_domains_service.indexer.exists(index):
        try:
            current_domains_service.indexer.bulk_index(domain_ids)
        except search.exceptions.ConflictError as e:
            current_app.logger.warn(f"Could not bulk-reindex groups: {e}")


@shared_task(ignore_result=True)
def delete_domains(domain_ids):
    """Delete domains from index."""
    index = current_domains_service.record_cls.index
    if current_domains_service.indexer.exists(index):
        try:
            current_domains_service.indexer.bulk_delete(domain_ids)
        except search.exceptions.ConflictError as e:
            current_app.logger.warn(f"Could not bulk-unindex groups: {e}")
