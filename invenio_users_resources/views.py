# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio module providing management APIs for users and roles/groups."""

from flask import Blueprint, render_template
from flask_babelex import gettext as _

def create_users_resources_bp(app):
    """Create the users resources blueprint."""

    # TODO create actual blueprint for the resources
    blueprint = Blueprint(
        'invenio_users_resources',
        __name__,
    )

    return blueprint
