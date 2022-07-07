# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Search dumpers, for transforming to and from versions to index."""

from .email import EmailFieldDumperExt

__all__ = ("EmailFieldDumperExt",)
