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
