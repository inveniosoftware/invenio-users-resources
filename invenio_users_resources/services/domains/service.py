# SPDX-FileCopyrightText: 2022 KTH Royal Institute of Technology
# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-FileCopyrightText: 2024 CERN.
# SPDX-FileCopyrightText: 2022 European Union.
# SPDX-License-Identifier: MIT

"""Domains service."""

from invenio_accounts.models import Domain
from invenio_db import db
from invenio_records_resources.services import RecordService


class DomainsService(RecordService):
    """Domains service."""

    def rebuild_index(self, identity, uow=None):
        """Reindex all user groups managed by this service."""
        domains = db.session.query(Domain.domain).yield_per(1000)
        self.indexer.bulk_index([r[0] for r in domains])
        return True
