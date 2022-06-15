# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User groups service configuration."""

from flask_babelex import lazy_gettext as _
from invenio_records_resources.services import (
    RecordServiceConfig,
    SearchOptions,
    pagination_links,
)
from invenio_records_resources.services.records.params import QueryStrParam, SortParam
from invenio_records_resources.services.records.queryparser import QueryParser

from ...records.api import GroupAggregate
from ..common import Link
from ..params import FixedPagination
from ..permissions import GroupsPermissionPolicy
from ..schemas import GroupSchema
from .results import GroupItem, GroupList


class GroupSearchOptions(SearchOptions):
    """Search options."""

    pagination_options = {
        "default_results_per_page": 10,
        "default_max_results": 10,
    }

    query_parser_cls = QueryParser.factory(fields=["id", "name"])

    sort_default = "bestmatch"
    sort_default_no_query = "name"
    sort_options = {
        "bestmatch": dict(
            title=_("Best match"),
            fields=["_score"],  # ES defaults to desc on `_score` field
        ),
        "name": dict(  # TODO: add asc/desc
            title=_("Name"),
            fields=["name.keyword"],
        ),
    }

    params_interpreters_cls = [
        QueryStrParam,
        SortParam,
        FixedPagination,
    ]


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
