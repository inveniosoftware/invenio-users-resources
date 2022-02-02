# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio module providing management APIs for users and roles/groups."""

from . import config
from .resources import UserGroupsResource, UserGroupsResourceConfig, \
    UsersResource, UsersResourceConfig
from .services import UserGroupsService, UserGroupsServiceConfig, \
    UsersService, UsersServiceConfig


class InvenioUsersResources(object):
    """Invenio-Users-Resources extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.init_services(app)
        self.init_resources(app)
        app.extensions["invenio-users-resources"] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("USERS_RESOURCES_"):
                app.config.setdefault(k, getattr(config, k))

    def init_services(self, app):
        """Initialize the services for users and user groups."""
        self.users_service = UsersService(config=UsersServiceConfig)
        self.user_groups_service = UserGroupsService(
            config=UserGroupsServiceConfig
        )

    def init_resources(self, app):
        """Initialize the resources for users and user groups."""
        self.users_resource = UsersResource(
            service=self.users_service,
            config=UsersResourceConfig,
        )
        self.user_groups_resource = UserGroupsResource(
            service=self.user_groups_service,
            config=UserGroupsResourceConfig,
        )
