# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 CERN.
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Domains service tasks."""

import requests
from celery import shared_task
from flask import current_app
from invenio_accounts.models import Domain, DomainCategory, DomainStatus, User
from invenio_db import db
from invenio_search.engine import search

from ...proxies import current_domains_service, current_users_service


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


@shared_task
def import_domain_blocklist(url, source_name):
    """Run import of domain blocklist.

    Marks domain as a spammer and blocks account registration from that domain.
    If domain already exists, it simply flags the domain, but does not block
    the domain.
    """
    spammer_category = DomainCategory.get("spammer")
    changed = set()

    for d in download_blocklist(url):
        if d.endswith("."):
            d = d[:-1]
        domain = Domain.query.filter_by(domain=d).one_or_none()
        if domain is None:
            current_app.logger.info(f"Creating {d}")
            try:
                domain = Domain.create(
                    d,
                    status=DomainStatus.blocked,
                    flagged=True,
                    flagged_source=source_name,
                    category=spammer_category.id,
                )
                db.session.commit()
                changed.add((domain.id, d))
            except Exception:
                current_app.logger.error(f"Error creating domain {d}")
                pass
        elif domain.flagged != True:
            current_app.logger.info(f"Updating ({domain.status}) {d}")
            domain.flagged = True
            domain.flagged_source = source_name
            db.session.commit()
            changed.add((domain.id, d))

    if len(changed) > 0:
        current_app.logger.info("Reindexing changed domains...")
        current_domains_service.indexer.bulk_index([x[0] for x in changed])

        current_app.logger.info("Reindexing users in changed domains...")
        for dummy, d in changed:
            users = db.session.query(User.id).filter(User.domain == d).yield_per(1000)
            current_users_service.indexer.bulk_index([u.id for u in users])


def download_blocklist(url):
    """Download domain blocklist from a given URL."""
    current_app.logger.info(f"Downloading {url}...")
    response = requests.get(url)
    if response.status_code != 200:
        current_app.logger.error(
            f"Failed to download {url}",
            extra={"url": url, "status_code": response.status_code},
        )
        return []

    # Parse file
    content = response.content.decode("utf-8")
    return {line.rstrip() for line in content.splitlines()}
