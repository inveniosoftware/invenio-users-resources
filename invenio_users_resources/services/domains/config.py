# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2024 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Domains service configuration."""

from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services import (
    RecordServiceConfig,
    SearchOptions,
    pagination_links,
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
from ..common import Link
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


def domainvar(obj, vars):
    """Add domain into link vars."""
    vars["domain"] = obj.domain


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
        "self": Link("{+api}/domains/{domain}", vars=domainvar),
        "admin_self_html": Link(
            "{+ui}/administration/domains/{domain}", vars=domainvar
        ),
        "admin_users_html": Link(
            "{+ui}/administration/users?q=domain:{domain}", vars=domainvar
        ),
    }
    links_search = pagination_links("{+api}/domains{?args*}")

    components = [
        DomainComponent,
    ]
