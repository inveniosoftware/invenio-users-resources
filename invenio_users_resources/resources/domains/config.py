# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Domains resource config."""

import marshmallow as ma
from flask_resources import (
    JSONDeserializer,
    JSONSerializer,
    RequestBodyParser,
    ResponseHandler,
)
from invenio_records_resources.resources import RecordResourceConfig


#
# Resource config
#
class DomainsResourceConfig(RecordResourceConfig):
    """User groups resource configuration."""

    blueprint_name = "domains"
    url_prefix = "/domains"

    # Request parsing
    request_headers = {}
    request_body_parsers = {
        "application/vnd.inveniordm.v1+json": RequestBodyParser(JSONDeserializer()),
        "application/json": RequestBodyParser(JSONDeserializer()),
    }
    default_content_type = "application/vnd.inveniordm.v1+json"

    # Response handling
    response_handlers = {
        "application/vnd.inveniordm.v1+json": ResponseHandler(JSONSerializer()),
        "application/json": ResponseHandler(JSONSerializer()),
    }
    default_accept_mimetype = "application/vnd.inveniordm.v1+json"
