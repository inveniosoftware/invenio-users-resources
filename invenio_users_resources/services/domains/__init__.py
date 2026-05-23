# SPDX-FileCopyrightText: 2024 CERN.
# SPDX-License-Identifier: MIT

"""Services for domains."""

from .config import DomainsServiceConfig
from .service import DomainsService

__all__ = (
    "DomainsService",
    "DomainsServiceConfig",
)
