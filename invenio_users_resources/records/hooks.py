# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio users DB hooks."""

from invenio_accounts.models import Domain, Role, User
from invenio_accounts.proxies import current_db_change_history

from ..services.domains.tasks import delete_domains, reindex_domains
from ..services.groups.tasks import reindex_groups, unindex_groups
from ..services.users.tasks import reindex_users, unindex_users


def pre_commit(sender, session):
    """Find out which entities need indexing before commit."""
    # it seems that the {dirty,new,deleted} sets aren't populated
    # in after_commit anymore, that's why we need to collect the
    # information here.
    # session is a scoped_session and does not have _model_changes,
    # so we have to rely only on .dirty
    updated = session.dirty.union(session.new)
    deleted = session.deleted
    sid = id(session)
    # flush the session s.t. related models are queryable
    session.flush()

    # users need to be reindexed if their user model was updated, or
    # their profile was changed (or even possibly deleted)
    for item in updated:
        if isinstance(item, User):
            current_db_change_history.add_updated_user(sid, item.id)
        if isinstance(item, Role):
            current_db_change_history.add_updated_role(sid, item.id)
        if isinstance(item, Domain):
            current_db_change_history.add_updated_domain(sid, item.id)

    for item in deleted:
        if isinstance(item, User):
            current_db_change_history.add_deleted_user(sid, item.id)
        if isinstance(item, Role):
            current_db_change_history.add_deleted_role(sid, item.id)
        if isinstance(item, Domain):
            current_db_change_history.add_deleted_domain(sid, item.id)


def post_commit(sender, session):
    """Reindex all modified users and roles after the DB commit."""
    # since this function is called after the commit, no more
    # DB operations are allowed here, not even lazy-loading of
    # properties!
    sid = id(session)

    if current_db_change_history.sessions.get(sid):
        # Handle updates
        user_ids_updated = list(current_db_change_history.sessions[sid].updated_users)
        if user_ids_updated:
            reindex_users.delay(user_ids_updated)

        group_ids_updated = list(current_db_change_history.sessions[sid].updated_roles)
        if group_ids_updated:
            reindex_groups.delay(group_ids_updated)

        domain_ids_updated = list(
            current_db_change_history.sessions[sid].updated_domains
        )
        if domain_ids_updated:
            reindex_domains.delay(domain_ids_updated)

        # Handle deletes
        user_ids_deleted = list(current_db_change_history.sessions[sid].deleted_users)
        if user_ids_deleted:
            unindex_users.delay(user_ids_deleted)

        group_ids_deleted = list(current_db_change_history.sessions[sid].deleted_roles)
        if group_ids_deleted:
            unindex_groups.delay(group_ids_deleted)

        domain_ids_deleted = list(
            current_db_change_history.sessions[sid].deleted_domains
        )
        if domain_ids_deleted:
            delete_domains.delay(domain_ids_deleted)
