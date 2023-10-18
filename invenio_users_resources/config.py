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
    "sort": [
        "email",
        "username",
        "id",
        "email_domain",
    ],
    "facets": ["email_domain", "affiliations"],
}
"""User search configuration (i.e list of banners)."""

USERS_RESOURCES_SORT_OPTIONS = {
    "id": dict(
        title=_("ID"),
        fields=["id"],
    ),
    "username": dict(
        title=_("Username"),
        fields=["username"],
    ),
    "email": dict(
        title=_("Email"),
        fields=["email"],
    ),
    "email_domain": dict(
        title=_("Email domain"),
        fields=["email.domain"],
    ),
}
"""Definitions of available Users sort options. """

USERS_RESOURCES_SEARCH_FACETS = {
    "email_domain": {
        "facet": facets.email_domain,
        "ui": {
            "field": "email.domain",
        },
    },
    "affiliations": {
        "facet": facets.affiliations,
        "ui": {
            "field": "profile.affiliations.keyword",
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
