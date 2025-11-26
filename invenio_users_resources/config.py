# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio module providing management APIs for users and roles/groups."""

from invenio_i18n import lazy_gettext as _
from marshmallow import Schema, fields, validate

from invenio_users_resources.services.domains import facets as domainfacets
from invenio_users_resources.services.groups import facets as groupsfacets
from invenio_users_resources.services.schemas import UserSchema
from invenio_users_resources.services.users import facets

USERS_RESOURCES_AVATAR_COLORS = [
    "#e06055",
    "#ff8a65",
    "#e91e63",
    "#f06292",
    "#673ab7",
    "#ba68c8",
    "#7986cb",
    "#3f51b5",
    "#5e97f6",
    "#00a4e4",
    "#4dd0e1",
    "#0097a7",
    "#d4e157",
    "#aed581",
    "#57bb8a",
    "#4db6ac",
    "#607d8b",
    "#795548",
    "#a1887f",
    "#fdd835",
    "#a3a3a3",
    "#556c60",
    "#605264",
    "#923035",
    "#915a30",
    "#55526f",
    "#67635a",
]

USERS_RESOURCES_SERVICE_SCHEMA = UserSchema
"""Schema used by the users service."""

USERS_RESOURCES_SEARCH = {
    "sort": ["bestmatch", "username", "email", "domain", "newest", "oldest", "updated"],
    "facets": ["status", "visibility", "domain_status", "domain", "affiliations"],
}
"""User search configuration."""

USERS_RESOURCES_SORT_OPTIONS = {
    "bestmatch": dict(
        title=_("Best match"),
        fields=["_score"],
    ),
    "username": dict(
        title=_("Username"),
        fields=["username.keyword", "-created"],
    ),
    "email": dict(
        title=_("Email"),
        fields=["email_hidden", "-created"],
    ),
    "domain": dict(
        title=_("Domain"),
        fields=["domain", "-created"],
    ),
    "newest": dict(
        title=_("Newest"),
        fields=["-created"],
    ),
    "oldest": dict(
        title=_("Oldest"),
        fields=["created"],
    ),
    "updated": dict(
        title=_("Recently updated"),
        fields=["-updated"],
    ),
}
"""Definitions of available Users sort options. """

USERS_RESOURCES_SEARCH_FACETS = {
    "domain": {
        "facet": facets.domain,
        "ui": {
            "field": "domain",
        },
    },
    "domain_status": {
        "facet": facets.domain_status,
        "ui": {
            "field": "domain_status",
        },
    },
    "affiliations": {
        "facet": facets.affiliations,
        "ui": {
            "field": "profile.affiliations.keyword",
        },
    },
    "status": {
        "facet": facets.status,
        "ui": {
            "field": "status",
        },
    },
    "visibility": {
        "facet": facets.visibility,
        "ui": {
            "field": "visibility",
        },
    },
}
"""Invenio requests facets."""

USERS_RESOURCES_MODERATION_LOCK_DEFAULT_TIMEOUT = 30
"""Default timeout, in seconds, to lock a user when moderating."""

USERS_RESOURCES_MODERATION_LOCK_RENEWAL_TIMEOUT = 120
"""Renewal timeout, in seconds, to increase the lock time for a user when moderating."""


USERS_RESOURCES_DOMAINS_SEARCH = {
    "sort": [
        "bestmatch",
        "domain",
        "newest",
        "oldest",
        "updated",
        "num-users",
        "num-active",
        "num-inactive",
        "num-confirmed",
        "num-verified",
        "num-blocked",
    ],
    "facets": ["status", "flagged", "category", "organisation", "tld"],
}
"""User search configuration."""

USERS_RESOURCES_DOMAINS_SORT_OPTIONS = {
    "bestmatch": dict(
        title=_("Best match"),
        fields=["_score"],
    ),
    "domain": dict(
        title=_("Domain"),
        fields=["domain", "-created"],
    ),
    "newest": dict(
        title=_("Newest"),
        fields=["-created"],
    ),
    "oldest": dict(
        title=_("Oldest"),
        fields=["created"],
    ),
    "updated": dict(
        title=_("Recently updated"),
        fields=["-updated"],
    ),
    "num-users": dict(
        title=_("# Users"),
        fields=["-num_users"],
    ),
    "num-active": dict(
        title=_("# Active"),
        fields=["-num_active"],
    ),
    "num-inactive": dict(
        title=_("# Inactive"),
        fields=["-num_inactive"],
    ),
    "num-confirmed": dict(
        title=_("# Confirmed"),
        fields=["-num_confirmed"],
    ),
    "num-verified": dict(
        title=_("# Verified"),
        fields=["-num_verified"],
    ),
    "num-blocked": dict(
        title=_("# Blocked"),
        fields=["-num_blocked"],
    ),
}
"""Definitions of available Users sort options. """

USERS_RESOURCES_DOMAINS_SEARCH_FACETS = {
    "status": {
        "facet": domainfacets.status,
        "ui": {
            "field": "status",
        },
    },
    "flagged": {
        "facet": domainfacets.flagged,
        "ui": {
            "field": "flagged",
        },
    },
    "category": {
        "facet": domainfacets.category,
        "ui": {
            "field": "category",
        },
    },
    "organisation": {
        "facet": domainfacets.organisation,
        "ui": {
            "field": "organisation",
        },
    },
    "tld": {
        "facet": domainfacets.tld,
        "ui": {
            "field": "tld",
        },
    },
}
"""Invenio domains facets."""

USERS_RESOURCES_GROUPS_ADMIN_SORT_OPTIONS = {
    "bestmatch": dict(
        title=_("Best match"),
        fields=["_score"],
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
        fields=["-is_managed", "name.keyword"],
    ),
    "unmanaged": dict(
        title=_("Unmanaged first"),
        fields=["is_managed", "name.keyword"],
    ),
}
"""Definitions of available Groups sort options for admin interface. """

USERS_RESOURCES_GROUPS_ADMIN_SEARCH = {
    "sort": ["bestmatch", "name", "name_desc", "managed", "unmanaged"],
    "facets": ["is_managed"],
}
"""Invenio groups admin search configuration."""

USERS_RESOURCES_GROUPS_ADMIN_FACETS = {
    "is_managed": {
        "facet": groupsfacets.is_managed,
        "ui": {
            "field": "is_managed",
        },
    },
}
"""Invenio groups admin search configuration."""

USERS_RESOURCES_PROTECTED_GROUP_NAMES = [
    "admin",
    "administration",
    "superuser-access",
    "administration-moderation",
]
"""Group identifiers that cannot be mutated via API (system process only).

References:
- superuser-access: https://github.com/inveniosoftware/invenio-access/blob/master/invenio_access/permissions.py
- administration: https://github.com/inveniosoftware/invenio-administration/blob/master/invenio_administration/permissions.py
- admin: https://github.com/inveniosoftware/invenio-cli/blob/master/invenio_cli/commands/services.py (created during instance setup)
- administration-moderation: https://github.com/inveniosoftware/invenio-users-resources/blob/master/invenio_users_resources/permissions.py
"""


class OrgPropsSchema(Schema):
    """Schema for validating domain org properties."""

    country = fields.String(validate=validate.Length(min=2, max=3))


USERS_RESOURCES_DOMAINS_ORG_SCHEMA = OrgPropsSchema
"""Domains organisation schema config."""

USERS_RESOURCES_GROUPS_ENABLED = True
"""Config to enable features related to existence of groups."""
