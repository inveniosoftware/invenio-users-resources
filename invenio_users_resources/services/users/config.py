# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022-2024 CERN.
# Copyright (C) 2024 KTH Royal Institute of Technology.
# Copyright (C) 2025 Northwestern University.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users service configuration."""

from invenio_accounts.utils import DomainStatus
from invenio_records_resources.services import (
    EndpointLink,
    RecordServiceConfig,
    pagination_endpoint_links,
)
from invenio_records_resources.services.base.config import (
    ConfiguratorMixin,
    FromConfig,
    FromConfigSearchOptions,
    SearchOptionsMixin,
)
from invenio_records_resources.services.records.config import SearchOptions
from invenio_records_resources.services.records.params import (
    FacetsParam,
    PaginationParam,
    QueryStrParam,
    SortParam,
)
from invenio_records_resources.services.records.queryparser import (
    FieldValueMapper,
    QueryParser,
    SearchFieldTransformer,
    SuggestQueryParser,
)
from luqum.tree import Word

from ...records.api import UserAggregate
from ..common import EndpointLinkWithId, vars_func_set_querystring
from ..params import FixedPagination
from ..permissions import UsersPermissionPolicy
from ..schemas import UserSchema
from .results import UserItem, UserList
from .search_params import ModerationFilterParam


def can_manage(obj, ctx):
    """Check if user can manage."""
    from invenio_users_resources.proxies import current_users_service

    return current_users_service.check_permission(ctx["identity"], "manage")


def word_domain_status(node):
    """Quote DOIs."""
    val = node.value
    if val in ["verified", "blocked", "moderated", "new"]:
        val = DomainStatus[node.value].value
    return Word(f"{val}")


class UserSearchOptions(SearchOptions, SearchOptionsMixin):
    """Search options."""

    pagination_options = {
        "default_results_per_page": 10,
        "default_max_results": 10,
    }
    # ATTENTION: Risk of leaking account information!!!
    # The user search needs to be highly restricted to avoid leaking
    # account information, hence do not edit here unless you are
    # absolutely sure what you're doing.
    suggest_parser_cls = SuggestQueryParser.factory(
        tree_transformer_cls=SearchFieldTransformer,
        fields=[
            "username^2",
            "email^2",
            "profile.full_name^10",
            "profile.affiliations",
        ],
        # Only public emails because hidden emails are stored in email_hidden field.
        allow_list=["username", "email"],
        mapping={
            "affiliation": "profile.affiliations",
            "affiliations": "profile.affiliations",
            "full_name": "profile.full_name",
            "fullname": "profile.full_name",
            "name": "profile.full_name",
        },
        type="most_fields",  # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-multi-match-query.html#multi-match-types
        fuzziness="AUTO",  # https://www.elastic.co/guide/en/elasticsearch/reference/current/common-options.html#fuzziness
    )

    params_interpreters_cls = [
        QueryStrParam,
        SortParam,
        FixedPagination,
        FacetsParam,
    ]


class AdminUserSearchOptions(UserSearchOptions):
    """Admin Search options."""

    pagination_options = {
        "default_results_per_page": 20,
        "default_max_results": 10_000,
    }

    query_parser_cls = QueryParser.factory(
        tree_transformer_cls=SearchFieldTransformer,
        fields=[
            "username^3",
            "email_hidden^3",
            "domain^2",
            "profile.full_name^3",
            "profile.affiliations",
        ],
        allow_list=[
            "id",
            "username",
            "domain",
            "email_hidden",
            "profile.full_name",
            "profile.affiliations",
            "created",
            "updated",
            "confirmed",
            "confirmed_at",
            "blocked_at",
            "verified_at",
            "preferences.visibility",
            "preferences.email_visibility",
            "visibility",
            "status",
            "current_login_at",
            "identities.github",
            "identities.orcid",
            "identities.openaire",
            "domaininfo.status",
            "domaininfo.flagged",
            "domaininfo.tld",
            "domaininfo.category",
        ],
        mapping={
            "affiliation": "profile.affiliations",
            "affiliations": "profile.affiliations",
            "full_name": "profile.full_name",
            "fullname": "profile.full_name",
            "name": "profile.full_name",
            "email": "email_hidden",
            "visibility": "preferences.visibility",
            "email_visibility": "preferences.email_visibility",
            "github": "identities.github",
            "orcid": "identities.orcid",
            "openaire": "identities.openaire",
            "domain.status": FieldValueMapper(
                "domaininfo.status", word=word_domain_status
            ),
            "domain.tld": "domaininfo.tld",
            "domain.category": "domaininfo.category",
            "domain.flagged": "domaininfo.flagged",
        },
    )

    params_interpreters_cls = [
        QueryStrParam,
        SortParam,
        PaginationParam,
        FacetsParam,
        ModerationFilterParam.factory(param="is_blocked", field="blocked_at"),
        ModerationFilterParam.factory(param="is_verified", field="verified_at"),
        ModerationFilterParam.factory(param="is_active", field="active"),
    ]


class UsersServiceConfig(RecordServiceConfig, ConfiguratorMixin):
    """Requests service configuration."""

    # common configuration
    permission_policy_cls = UsersPermissionPolicy
    result_item_cls = UserItem
    result_list_cls = UserList
    # We're not allowing override of options to prevent risk of
    # leaking account information.
    search = UserSearchOptions

    # For admin user
    search_all = FromConfigSearchOptions(
        "USERS_RESOURCES_SEARCH",
        "USERS_RESOURCES_SORT_OPTIONS",
        "USERS_RESOURCES_SEARCH_FACETS",
        search_option_cls=AdminUserSearchOptions,
    )
    # search = UserSearchOptions
    # specific configuration
    service_id = "users"
    record_cls = UserAggregate
    schema = FromConfig("USERS_RESOURCES_SERVICE_SCHEMA", UserSchema)
    indexer_queue_name = "users"
    index_dumper = None

    # links configuration
    links_item = {
        "self": EndpointLinkWithId("users.read"),
        "avatar": EndpointLinkWithId("users.avatar"),
        "records_html": EndpointLink(
            "invenio_search_ui.search",
            vars=vars_func_set_querystring(
                lambda obj, vars: {"q": f"parent.access.owned_by.user:{obj.id}"}
            ),
        ),
        "admin_records_html": EndpointLink(
            "administration.records",
            vars=vars_func_set_querystring(
                lambda obj, vars: {
                    "q": f"parent.access.owned_by.user:{obj.id}",
                    "f": "allversions",
                }
            ),
            when=can_manage,
        ),
        "admin_drafts_html": EndpointLink(
            "administration.drafts",
            vars=vars_func_set_querystring(
                lambda obj, vars: {
                    "q": f"parent.access.owned_by.user:{obj.id}",
                    "f": "allversions",
                }
            ),
            when=can_manage,
        ),
        "admin_moderation_html": EndpointLink(
            "administration.moderation",
            vars=vars_func_set_querystring(
                lambda obj, vars: {"q": f"topic.user:{obj.id}"}
            ),
            when=can_manage,
        ),
        # TODO missing moderation actions based on permissions
    }

    links_search = pagination_endpoint_links("users.search")

    components = [
        # order of components are important!
    ]
