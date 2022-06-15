# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio users DB hooks."""

from invenio_accounts.models import Role, User
from invenio_accounts.proxies import current_db_change_history

from ..services.groups.tasks import reindex_group, unindex_group
from ..services.users.tasks import reindex_user, unindex_user


def pre_commit(sender, session):
    """Find out which entities need indexing before commit."""
    # it seems that the {dirty,new,deleted} sets aren't populated
    # in after_commit anymore, that's why we need to collect the
    # information here.
    # session is a scoped_session and does not have _model_changes
    # so we have rely only on .dirty
    updated = session.dirty.union(session.new)
    deleted = session.deleted
    sid = id(session)
    # flush the session s.t. related models are queryable
    session.flush()

    # users need to be reindexed if their user model was updated, or
    # their profile was changed (or even possibly deleted)
    current_db_change_history.updated_users[sid].extend(
        [u.id for u in updated if isinstance(u, User)]
    )
    current_db_change_history.updated_roles[sid].extend(
        [r.id for r in updated if isinstance(r, Role)]
    )

    current_db_change_history.deleted_users[sid].extend(
        [u.id for u in deleted if isinstance(u, User)]
    )
    current_db_change_history.deleted_roles[sid].extend(
        [r.id for r in deleted if isinstance(r, Role)]
    )


def post_commit(sender, session):
    """Reindex all modified users and roles after the DB commit."""
    # since this function is called after the commit, no more
    # DB operations are allowed here, not even lazy-loading of
    # properties!
    sid = id(session)
    for user_id in current_db_change_history.updated_users[sid]:
        reindex_user.delay(user_id)

    for role_id in current_db_change_history.updated_roles[sid]:
        reindex_group.delay(role_id)

    for user_id in current_db_change_history.deleted_users[sid]:
        unindex_user.delay(user_id)
    for role_id in current_db_change_history.deleted_roles[sid]:
        unindex_group.delay(role_id)

    current_db_change_history._clear_dirty_sets(session)
