# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User groups service configuration."""

from invenio_records_resources.services import (
    RecordServiceConfig,
    SearchOptions,
    pagination_links,
)

from ...records.api import GroupAggregate
from ..common import Link
from ..permissions import GroupsPermissionPolicy
from ..schemas import GroupSchema
from .results import GroupItem, GroupList


class GroupSearchOptions(SearchOptions):
    """Search options."""

    # TODO search params
    params_interpreters_cls = SearchOptions.params_interpreters_cls


class GroupsServiceConfig(RecordServiceConfig):
    """Requests service configuration."""

    # common configuration
    permission_policy_cls = GroupsPermissionPolicy
    result_item_cls = GroupItem
    result_list_cls = GroupList
    search = GroupSearchOptions

    # specific configuration
    service_id = "groups"
    record_cls = GroupAggregate
    schema = GroupSchema
    indexer_queue_name = "groups"
    index_dumper = None

    # links configuration
    links_item = {
        "self": Link("{+api}/groups/{id}"),
        "avatar": Link("{+api}/groups/{id}/avatar.svg"),
    }
    links_search = pagination_links("{+api}/groups{?args*}")

    components = [
        # Order of components are important!
    ]
