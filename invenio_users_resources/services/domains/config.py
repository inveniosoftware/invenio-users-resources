# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2024 CERN.
# Copyright (C) 2023 Graz University of Technology.
# Copyright (C) 2025 Northwestern University.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Domains service configuration."""

from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services import (
    EndpointLink,
    RecordEndpointLink,
    RecordServiceConfig,
    SearchOptions,
    pagination_endpoint_links,
)
from invenio_records_resources.services.base.config import (
    ConfiguratorMixin,
    FromConfigSearchOptions,
    SearchOptionsMixin,
)
from invenio_records_resources.services.records.params import (
    FacetsParam,
    PaginationParam,
    QueryStrParam,
    SortParam,
)
from invenio_records_resources.services.records.queryparser import QueryParser

from ...records.api import DomainAggregate
from ..common import vars_func_set_querystring
from ..permissions import DomainPermissionPolicy
from ..schemas import DomainSchema
from .components import DomainComponent


class DomainsSearchOptions(SearchOptions, SearchOptionsMixin):
    """Search options."""

    pagination_options = {
        "default_results_per_page": 30,
        "default_max_results": 1000,
    }

    query_parser_cls = QueryParser.factory(
        fields=[
            "id",
            "domain^3",
        ],
    )

    sort_default = "bestmatch"
    sort_default_no_query = "newest"

    params_interpreters_cls = [
        QueryStrParam,
        SortParam,
        PaginationParam,
        FacetsParam,
    ]


class DomainsServiceConfig(RecordServiceConfig, ConfiguratorMixin):
    """Requests service configuration."""

    # common configuration
    permission_policy_cls = DomainPermissionPolicy
    search = FromConfigSearchOptions(
        "USERS_RESOURCES_DOMAINS_SEARCH",
        "USERS_RESOURCES_DOMAINS_SORT_OPTIONS",
        "USERS_RESOURCES_DOMAINS_SEARCH_FACETS",
        search_option_cls=DomainsSearchOptions,
    )

    # specific configuration
    service_id = "domains"
    record_cls = DomainAggregate
    schema = DomainSchema
    indexer_queue_name = "domains"
    index_dumper = None

    # links configuration
    links_item = {
        "self": RecordEndpointLink("domains.read"),
        "admin_self_html": RecordEndpointLink("administration.domains_details"),
        "admin_users_html": EndpointLink(
            "administration.users",
            vars=vars_func_set_querystring(
                lambda obj, vars: {
                    "q": f"domain:{obj.domain}",
                }
            ),
        ),
    }
    links_search = pagination_endpoint_links("domains.search")

    components = [
        DomainComponent,
    ]
