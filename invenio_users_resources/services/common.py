# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Definitions that are used by both users and user groups services."""

from invenio_records_resources.services import Link as LinkBase


class Link(LinkBase):
    """Shortcut for writing links with IDs."""

    @staticmethod
    def vars(obj, vars):
        """Variables for the URI template."""
        vars.update({"id": obj.id})
