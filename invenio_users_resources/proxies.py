# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Proxies for accessing the current Users-Resources extension."""

from flask import current_app
from werkzeug.local import LocalProxy

current_user_resources = LocalProxy(
    lambda: current_app.extensions["invenio-users-resources"]
)
"""Proxy for the instantiated Users-Resources extension."""

current_users_service = LocalProxy(
    lambda: current_app.extensions["invenio-users-resources"].users_service
)
"""Proxy for the currently instantiated users service."""

current_groups_service = LocalProxy(
    lambda: current_app.extensions["invenio-users-resources"].groups_service
)
"""Proxy for the currently instantiated user groups service."""
