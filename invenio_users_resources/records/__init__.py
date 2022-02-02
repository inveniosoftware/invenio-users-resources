# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Data-layer definitions for user and group management in Invenio."""

from .api import GroupAggregate, UserAggregate

__all__ = (
    "UserAggregate",
    "GroupAggregate",
)
