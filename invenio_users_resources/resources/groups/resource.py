# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 European Union.
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""User groups resource."""

from flask import g, send_file
from flask_resources import resource_requestctx, response_handler, route
from invenio_records_resources.resources import RecordResource
from invenio_records_resources.resources.records.resource import (
    request_data,
    request_search_args,
    request_view_args,
)
from invenio_records_resources.resources.records.utils import search_preference


#
# Resource
#
class GroupsResource(RecordResource):
    """Resource for user groups."""

    def create_url_rules(self):
        """Create the URL rules for the user groups resource."""
        routes = self.config.routes
        return [
            route("GET", routes["list"], self.search),
            route("POST", routes["list"], self.create),
            route("GET", routes["item"], self.read),
            route("PUT", routes["item"], self.update),
            route("DELETE", routes["item"], self.delete),
            route("GET", routes["item-avatar"], self.avatar),
        ]

    @request_search_args
    @request_view_args
    @response_handler(many=True)
    def search(self):
        """Perform a search over the groups."""
        hits = self.service.search(
            identity=g.identity,
            params=resource_requestctx.args,
            search_preference=search_preference(),
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

    @request_data
    @response_handler()
    def create(self):
        """Create a group."""
        item = self.service.create(
            identity=g.identity,
            data=resource_requestctx.data or {},
        )
        return item.to_dict(), 201

    @request_view_args
    @request_data
    @response_handler()
    def update(self):
        """Update a group."""
        item = self.service.update(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
            data=resource_requestctx.data or {},
        )
        return item.to_dict(), 200

    @request_view_args
    def delete(self):
        """Delete a group."""
        self.service.delete(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return "", 204

    @request_view_args
    def avatar(self):
        """Get a groups's avatar."""
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
            max_age=86400 * 7,
        )
