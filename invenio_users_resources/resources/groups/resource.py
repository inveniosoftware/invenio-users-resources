# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User groups resource."""


from flask import g
from flask_resources import resource_requestctx, response_handler, route
from invenio_records_resources.resources import RecordResource
from invenio_records_resources.resources.records.resource import \
    request_search_args, request_view_args
from invenio_records_resources.resources.records.utils import es_preference


#
# Resource
#
class GroupsResource(RecordResource):
    """Resource for user groups."""

    def p(prefix, route):
        """Prefix a route with the URL prefix"""
        return f"{prefix}{route}"

    def create_url_rules(self):
        """Create the URL rules for the user groups resource."""
        routes = self.config.routes
        prefix = self.config.url_prefix
        return [
            route("GET", self.p(prefix, routes["list"]), self.search),
            route("GET", self.p(prefix, routes["item"]), self.read),
            route("GET", self.p(prefix, routes["avatar"]), self.avatar),
        ]

    @request_search_args
    @request_view_args
    @response_handler(many=True)
    def search(self):
        """Perform a search over the groups."""
        hits = self.service.search(
            identity=g.identity,
            params=resource_requestctx.args,
            es_preference=es_preference(),
        )
        return hits.to_dict(), 200

    @request_view_args
    @response_handler()
    def read(self):
        """Read a group."""
        item = self.service.read(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return item.to_dict(), 200

    @request_view_args
    @response_handler()
    def avatar(self):
        """Get a group's avatar."""
        item = self.service.get_avatar(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return item.to_dict(), 200
