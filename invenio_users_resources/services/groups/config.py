# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
# Copyright (C) 2023 Graz University of Technology.
# Copyright (C) 2025 KTH Royal Institute of Technology.
# Copyright (C) 2025 Northwestern University.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User groups service configuration."""

from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services import (
    RecordServiceConfig,
    SearchOptions,
    pagination_endpoint_links,
)
from invenio_records_resources.services.base.config import ConfiguratorMixin
from invenio_records_resources.services.records.params import (
    FacetsParam,
    QueryStrParam,
    SortParam,
)
from invenio_records_resources.services.records.queryparser import QueryParser

from ...records.api import GroupAggregate
from ..common import EndpointLinkWithId
from ..params import FixedPagination
from ..permissions import GroupsPermissionPolicy
from ..schemas import GroupSchema
from . import facets as groups_facets
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
        "name": dict(
            title=_("Name (A-Z)"),
            fields=["name.keyword"],
        ),
        "name_desc": dict(
            title=_("Name (Z-A)"),
            fields=["-name.keyword"],
        ),
        "managed": dict(
            title=_("Managed first"),
            fields=["-is_managed"],
        ),
        "unmanaged": dict(
            title=_("Unmanaged first"),
            fields=["is_managed"],
        ),
    }

    facets = {
        "is_managed": groups_facets.is_managed,
    }

    params_interpreters_cls = [
        QueryStrParam,
        SortParam,
        FixedPagination,
        FacetsParam,
    ]


class GroupsServiceConfig(RecordServiceConfig, ConfiguratorMixin):
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
        "self": EndpointLinkWithId("groups.read"),
        "avatar": EndpointLinkWithId("groups.avatar"),
    }
    links_search = pagination_endpoint_links("groups.search")

    components = [
        # Order of components are important!
    ]
