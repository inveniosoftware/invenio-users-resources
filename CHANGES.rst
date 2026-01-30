..
    Copyright (C) 2023-2025 CERN.
    Copyright (C) 2024-2026 Graz University of Technology.
    Copyright (C) 2026 Northwestern University.

    Invenio-Users-Resources is free software; you can redistribute it
    and/or modify it under the terms of the MIT License; see LICENSE file for
    more details.

Changes
=======

Version v10.0.0 (released 2026-01-30)

- chore(setup): bump dependencies
- chore(black): update formatting to >= 26.0
- fix: DeprecationWarning
- fix(chore): DeprecationWarning stdlib
- refactor: move to context_schema
- chore: replace deprecated logger.warn->warning
- chore+fix: replace usage of Link by EndpointLink and co


Version vNext (released YYYY-mm-dd)

- chore+fix: replace usage of Link by EndpointLink and co.
- chore: replace deprecated logger.warn->warning

Version v9.0.3 (released 2025-11-12)

- setup: bump major version of `invenio-oauthclient`

Version v9.0.2 (released 2025-10-02)

- fix(services.config): boost full_name for better results

Version v9.0.1 (released 2025-09-24)

- fix(entity_resolvers): handle `None` user entity

Version v9.0.0 (released 2025-09-05)

- BREAKING CHANGE: restrict access to users item endpoint. Return 404 instead of 403
    to avoid users enumeration.
- Add Celery task to import domains blocklist.

Version v8.3.0 (released 2025-07-17)

- i18n: pulled translations

Version v8.2.0 (released 2025-07-14)

- chores: replaced importlib_xyz with importlib

Version v8.1.0 (released 2025-07-02)

- admin: remove flag to always show the admin panel
- moderation: add self-action prevention
- fix: avatar etags failing for accented people names
- generators: fix permission check using Permission

Version v8.0.0 (released 2025-06-03)

- setup: bump major dependencies
- fix: RemovedInMarshmallow4Warning

Version v7.1.0 (released 2025-05-23)

- schemas: add email to system user schema

Version v7.0.0 (released 2025-02-13)

- Remove pre-release status.

Version v7.0.0.dev2 (released 2025-01-23)

Version 7.0.0.dev1 (released 2024-12-12)

- setup: change to reusable workflows
- setup: bump major dependencies

Version v6.1.3 (released 2024-12-12)

- services: explicitly set max results to 10,000 for admin user search

Version v6.1.2 (released 2024-12-12)

- service: remove max 100 results limit from admin user search

Version 6.1.1 (released 2024-11-05)

- global: make forward compatible to sqlalchemy >= 2

Version 6.1.0 (released 2024-09-17)

- services: add can search all permission for admin searches

Version 6.0.0 (released 2024-08-22)

- mappings: add analyzers and filters to improve results when searching users

Version 5.4.0 (released 2024-08-09)

- resources: use and adjust vnd.inveniordm.v1+json http accept header

Version 5.3.1 (released 2024-07-30)

- config: Update records_html link
- moderation: fix admin record / draft links

Version 5.3.0 (released 2024-06-04)

- installation: bump invenio-records-resources

Version 5.2.0 (released 2024-05-07)

- groups: add permissions and config to control groups feature flag

Version 5.1.1 (released 2024-04-02)

- config: enable user administration panel by default

Version 5.1.0 (released 2024-03-23)

- mappings: change "dynamic" values to string
- resolvers: pick resolved fields for group
- init: move record_once to finalize_app

Version 5.0.3 (released 2024-02-23)

- Fixed issue with notifications sending bad data to the service.

Version 5.0.2 (released 2024-02-19)

- Added Elasticsearch 7 mappings (not tested) to make deprecation of ES7
  easier.

Version 5.0.1 (released 2024-01-29)

- Added Elasticsearch 7 mappings (not tested) to make deprecation of ES7
  easier.

Version 5.0.0 (released 2024-01-29)

- add domains REST api and underlying service

- improved indexing, data flow and search

    * Refactors data flow and indexing so that the aggregate data model is
      in charge of all data parsing of the user and role model as well as
      indexing

    * Adds domain data and user identities and further attributes to the
      users index and makes them searchable for admins.

    * Fixes indexing/facets of email domain values.

    * Allows admins to search for restricted email addresses.

    * Add admin facets for domain, account status, domain status.

    * Add sort options to admin user search.

Version 4.0.0 (released 2024-01-29)

- installation: bump invenio-accounts and invenio-records-resources

Version 3.1.4 (2023-12-07)

- admin: fixed pagination and added id in search

Version 3.1.3 (2023-11-01)

- lock: add missing return statement to lock acquire

Version 3.1.2 (2023-10-17)

- Add support for user impersonation

Version 3.1.1 (2023-10-14)

- model: prevent flush on select queries

Version 3.1.0 (2023-10-06)

- notifications add email and conditional user recipient generators

Version 3.0.2 (2023-09-18)

- models: avoid flushing when getting records

Version 3.0.1 (2023-09-11)

- resolvers: fix links serialization
- resolvers: added ghost record for groups.

Version 3.0.0 (2023-09-08)

- mappings: updated analyzers for user emails (breaking change)

- administration: remove user admin views
- search: add email domain and affiliation facets
- resources: expose search all
- permissions: allow moderators to read emails

Version 2.6.0 (2023-08-30)

- user moderation: added lock mechanism

Version 2.5.0 (2023-08-21)

- user moderation: add resource endpoints
- user moderation: use datastore to deactivate users immediately

Version 2.4.0 (2023-08-17)

- template: set default value notifications enabled to True

Version 2.3.0 (2023-08-09)

- add actions registry
- add post action task operation on user block/restore/approve

Version 2.2.0 (2023-08-02)

- users: added user moderation actions
- users: added user moderation permissions
- users: added user moderation request entity resolution

Version 2.1.2 (2023-07-31)

- settings notifications: Layout and a11y fixes

Version 2.1.1 (2023-07-12)

- users: make username optional on expansion

Version 2.1.0 (2023-07-07)

- administration: add users administration panel

Version 2.0.1 (2023-07-05)

- fix post_commit hooks
- add translations

Version 2.0.0 (2023-06-30)

- changing the groups tasks interface to use bulk indexing as default

Version 1.9.0 (2023-06-15)

- groups: add description field
- hooks: refactor updating db change history on user or role change

Version 1.8.0 (2023-06-06)

- forms: add notification preferences form and handle
- ui: add notification settings preferences template
- config: allow configuration of user schema

Version 1.7.0 (2023-06-02)

- schemas: add system user schema

Version 1.6.0 (2023-05-05)

- add notifications
- add User notifications preferences

Version 1.5.1 (2023-04-26)

- add explicit dependency of invenio-accounts

Version 1.5.0 (2023-04-25)

- add user locale preferences

Version 1.4.0 (2023-04-25)

- upgrade invenio-records-resources

Version 1.3.0 (2023-04-20)

- upgrade invenio-records-resources
- fix query parser method call with allowlist

Version 1.2.0 (2023-03-24)

- bump invenio-records-resources to v2.0.0
- expand: add ghost user representation

Version 1.1.0 (released 2023-03-02)

- remove deprecated flask-babelex dependency and imports

Version 1.0.2 (released 2022-12-01)

- Add identity to links template expand method

Version 1.0.1 (released 2022-11-15)

- use bulk indexing for `rebuild_index` method in users/groups

Version 1.0.0

- Initial public release.
