# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2023-2024 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

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
