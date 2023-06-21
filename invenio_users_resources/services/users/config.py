# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users service configuration."""

from invenio_records_resources.services import RecordServiceConfig, pagination_links
from invenio_records_resources.services.base.config import (
    ConfiguratorMixin,
    FromConfig,
    FromConfigSearchOptions,
    SearchOptionsMixin,
)
from invenio_records_resources.services.records.config import SearchOptions
from invenio_records_resources.services.records.params import QueryStrParam, SortParam
from invenio_records_resources.services.records.queryparser import (
    QueryParser,
    SearchFieldTransformer,
)

from ...records.api import UserAggregate
from ..common import Link
from ..params import FixedPagination
from ..permissions import UsersPermissionPolicy
from ..schemas import UserSchema
from .results import UserItem, UserList


class UserSearchOptions(SearchOptions, SearchOptionsMixin):
    """Search options."""

    pagination_options = {
        "default_results_per_page": 10,
        "default_max_results": 10,
    }
    query_parser_cls = QueryParser.factory(
        tree_transformer_cls=SearchFieldTransformer,
        fields=["username^2", "email^2", "profile.full_name^3", "profile.affiliations"],
        allow_list=["username", "email"],  # mapped fields are added on the query parser
        mapping={
            "affiliation": "profile.affiliations",
            "affiliations": "profile.affiliations",
            "full_name": "profile.full_name",
            "fullname": "profile.full_name",
            "name": "profile.full_name",
        },
    )

    params_interpreters_cls = [
        QueryStrParam,
        SortParam,
        FixedPagination,
    ]


class UsersServiceConfig(RecordServiceConfig, ConfiguratorMixin):
    """Requests service configuration."""

    # common configuration
    permission_policy_cls = UsersPermissionPolicy
    result_item_cls = UserItem
    result_list_cls = UserList
    search = FromConfigSearchOptions(
        "USERS_RESOURCES_SEARCH",
        "USERS_RESOURCES_SORT_OPTIONS",
        None,
        search_option_cls=UserSearchOptions,
    )
    # specific configuration
    service_id = "users"
    record_cls = UserAggregate
    schema = FromConfig("USERS_RESOURCES_SERVICE_SCHEMA", UserSchema)
    indexer_queue_name = "users"
    index_dumper = None

    # links configuration
    links_item = {
        "self": Link("{+api}/users/{id}"),
        "avatar": Link("{+api}/users/{id}/avatar.svg"),
    }
    links_search = pagination_links("{+api}/users{?args*}")

    components = [
        # order of components are important!
    ]
