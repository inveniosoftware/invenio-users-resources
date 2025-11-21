# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2025 Northwestern University.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Definitions that are used by both users and user groups services."""

from invenio_records_resources.services import EndpointLink


class EndpointLinkWithId(EndpointLink):
    """Defines vars for endpoints whose routes use <id>."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super().__init__(*args, **kwargs)
        self._params.append("id")

    @staticmethod
    def vars(obj, vars):
        """Update vars used to expand/fill the link."""
        vars.update({"id": obj.id})


def vars_func_set_querystring(func_qs=lambda obj, vars: {}):
    """Fill in querystring parameters easily."""

    def _inner(obj, vars):
        vars.setdefault("args", {})
        vars["args"].update(func_qs(obj, vars))

    return _inner
