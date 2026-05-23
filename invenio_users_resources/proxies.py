# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-License-Identifier: MIT

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

current_domains_service = LocalProxy(
    lambda: current_app.extensions["invenio-users-resources"].domains_service
)
"""Proxy for the currently instantiated user groups service."""

current_actions_registry = LocalProxy(
    lambda: current_app.extensions["invenio-users-resources"].actions_registry
)
"""Proxy for the currently instantiated actions registry."""
