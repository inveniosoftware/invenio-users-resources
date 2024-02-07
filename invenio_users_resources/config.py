# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio module providing management APIs for users and roles/groups."""

from invenio_i18n import lazy_gettext as _

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
        fields=["username", "-created"],
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

USERS_RESOURCES_ADMINISTRATION_ENABLED = False
"""Enable the user administration"""

USERS_RESOURCES_MODERATION_LOCK_DEFAULT_TIMEOUT = 30
"""Default timeout, in seconds, to lock a user when moderating."""

USERS_RESOURCES_MODERATION_LOCK_RENEWAL_TIMEOUT = 120
"""Renewal timeout, in seconds, to increase the lock time for a user when moderating."""
