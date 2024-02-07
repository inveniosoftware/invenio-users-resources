# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 European Union.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users resource."""

from flask import g, send_file
from flask_resources import resource_requestctx, response_handler, route
from flask_security import impersonate_user
from invenio_records_resources.resources import RecordResource
from invenio_records_resources.resources.records.resource import (
    request_search_args,
    request_view_args,
)
from invenio_records_resources.resources.records.utils import search_preference


#
# Resource
#
class UsersResource(RecordResource):
    """Resource for users."""

    def p(self, prefix, route):
        """Prefix a route with the URL prefix."""
        return f"{prefix}{route}"

    def create_url_rules(self):
        """Create the URL rules for the users resource."""
        routes = self.config.routes
        return [
            route("GET", routes["list"], self.search),
            route("GET", routes["item"], self.read),
            route("GET", routes["item-avatar"], self.avatar),
            route("POST", routes["approve"], self.approve),
            route("POST", routes["block"], self.block),
            route("POST", routes["restore"], self.restore),
            route("POST", routes["deactivate"], self.deactivate),
            route("POST", routes["activate"], self.activate),
            route("POST", routes["impersonate"], self.impersonate),
            route("GET", routes["search_all"], self.search_all),
        ]

    @request_search_args
    @request_view_args
    @response_handler(many=True)
    def search(self):
        """Perform a search over users."""
        hits = self.service.search(
            identity=g.identity,
            params=resource_requestctx.args,
            search_preference=search_preference(),
        )
        return hits.to_dict(), 200

    @request_search_args
    @request_view_args
    @response_handler(many=True)
    def search_all(self):
        """Perform a search over users."""
        hits = self.service.search_all(
            identity=g.identity,
            params=resource_requestctx.args,
            search_preference=search_preference(),
        )
        return hits.to_dict(), 200

    @request_view_args
    @response_handler()
    def read(self):
        """Read a user."""
        item = self.service.read(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return item.to_dict(), 200

    @request_view_args
    def avatar(self):
        """Get a user's avatar."""
        avatar = self.service.read_avatar(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return send_file(
            avatar.bytes_io,
            mimetype=avatar.mimetype,
            as_attachment=False,
            download_name=avatar.name,
            etag=avatar.etag,
            last_modified=avatar.last_modified,
            max_age=avatar.max_age,
        )

    @request_view_args
    def approve(self):
        """Approve user."""
        self.service.approve(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return "", 200

    @request_view_args
    def block(self):
        """Block user."""
        self.service.block(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return "", 200

    @request_view_args
    def restore(self):
        """Restore user."""
        self.service.restore(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return "", 200

    @request_view_args
    def deactivate(self):
        """Deactive user."""
        self.service.deactivate(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return "", 200

    @request_view_args
    def activate(self):
        """Deactive user."""
        self.service.activate(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return "", 200

    @request_view_args
    def impersonate(self):
        """Impersonate the user."""
        user = self.service.can_impersonate(
            g.identity, resource_requestctx.view_args["id"]
        )
        if user:
            impersonate_user(user, g.identity)
        return "", 200
