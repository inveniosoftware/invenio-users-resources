# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Services for domains."""

from .config import DomainsServiceConfig
from .service import DomainsService

__all__ = (
    "DomainsService",
    "DomainsServiceConfig",
)
