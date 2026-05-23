# SPDX-FileCopyrightText: 2022 CERN.
# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-FileCopyrightText: 2023-2024 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Invenio module providing management APIs for users and roles/groups."""

from flask import Blueprint

blueprint = Blueprint(
    "invenio_users_resources",
    __name__,
    template_folder="templates",
    static_folder="static",
)


def create_users_resources_bp(app):
    """Create the users resource blueprint."""
    ext = app.extensions["invenio-users-resources"]
    return ext.users_resource.as_blueprint()


def create_groups_resources_bp(app):
    """Create the user groups resource blueprint."""
    ext = app.extensions["invenio-users-resources"]
    return ext.groups_resource.as_blueprint()


def create_domains_resources_bp(app):
    """Create the domains resource blueprint."""
    ext = app.extensions["invenio-users-resources"]
    return ext.domains_resource.as_blueprint()
