# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-FileCopyrightText: 2022-2026 CERN.
# SPDX-FileCopyrightText: 2024-2026 KTH Royal Institute of Technology.
# SPDX-FileCopyrightText: 2025 Northwestern University.
# SPDX-License-Identifier: MIT

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
    CompositeSuggestQueryParser,
    FieldValueMapper,
    QueryParser,
    SearchFieldTransformer,
)
from luqum.tree import Word

from ...proxies import current_users_service
from ...records.api import UserAggregate
from ..common import EndpointLinkWithId, vars_func_set_querystring
from ..params import FixedPagination
from ..permissions import UsersPermissionPolicy
from ..schemas import UserSchema
from .results import UserItem, UserList
from .search_params import ModerationFilterParam


def can_manage(obj, ctx):
    """Check if user can manage."""
    return current_users_service.check_permission(ctx["identity"], "manage")


def can_manage_groups(obj, ctx):
    """Check if user roles can be managed."""
    identity = ctx["identity"]
    actor_id = getattr(identity, "id", None)
    user_id = getattr(obj, "id", None)
    if actor_id is not None and user_id is not None and str(actor_id) == str(user_id):
        return False

    model = getattr(obj, "model", None)
    if getattr(model, "_model_obj", None) is not None:
        return current_users_service.check_permission(
            identity, "manage_groups", record=obj, actor_id=actor_id
        )

    return current_users_service.check_permission(identity, "manage_groups")


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
    suggest_parser_cls = CompositeSuggestQueryParser.factory(
        tree_transformer_cls=SearchFieldTransformer,
        fields=[
            "username.keyword^2",
            "username^2",
            "email.keyword^2",
            "email^2",
            "profile.full_name^10",
            "profile.affiliations",
        ],
        clauses=[
            # Exact username/email match always wins.
            {
                "type": "best_fields",
                "boost": 20,
                "fields": ["username.keyword", "email.keyword"],
            },
            # Multi-term queries spanning fields (e.g. full name + affiliation).
            {"type": "cross_fields", "boost": 3},
            # Rewards matches in multiple fields. No fuzziness here: with the ^10
            # full name boost and the edge-ngram index, fuzzy matches on other
            # people's names would outscore an exact username match.
            {"type": "most_fields", "boost": 1},
            # Typo tolerance on the edge-ngram text fields. Unboosted best_fields
            # keeps fuzzy noise below exact matches; prefix_length drops
            # first-character expansions, by far the noisiest.
            {
                "type": "best_fields",
                "boost": 1,
                "fuzziness": "AUTO",
                "prefix_length": 1,
                "fields": [
                    "username",
                    "email",
                    "profile.full_name",
                    "profile.affiliations",
                ],
            },
            # Typo tolerance on whole usernames/emails. Keyword terms are few
            # enough that rare usernames survive the fuzzy expansion cap, which
            # they don't on the edge-ngram fields.
            {
                "type": "best_fields",
                "boost": 3,
                "fuzziness": "AUTO",
                "prefix_length": 1,
                "fields": ["username.keyword", "email.keyword"],
            },
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
            "current_login_ip",
            "last_login_at",
            "last_login_ip",
            "login_count",
            "identities.github",
            "identities.orcid",
            "identities.openaire",
            "domaininfo.status",
            "domaininfo.flagged",
            "domaininfo.tld",
            "domaininfo.category",
            "roles",
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
            "role": "roles",
            "roles": "roles",
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
        "groups": EndpointLinkWithId("users.groups", when=can_manage_groups),
        # TODO missing moderation actions based on permissions
    }

    links_search = pagination_endpoint_links("users.search")

    components = [
        # order of components are important!
    ]
