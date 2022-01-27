# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users service configuration."""

from invenio_records_resources.services import RecordServiceConfig, \
    SearchOptions, pagination_links

from ..common import Link
from ..permissions import UsersPermissionPolicy
from .results import UserItem, UserList


class UserSearchOptions(SearchOptions):
    """Search options."""

    # TODO search params
    params_interpreters_cls = SearchOptions.params_interpreters_cls


class UsersServiceConfig(RecordServiceConfig):
    """Requests service configuration."""

    # common configuration
    permission_policy_cls = UsersPermissionPolicy
    result_item_cls = UserItem
    result_list_cls = UserList
    search = UserSearchOptions

    # specific configuration
    record_cls = None
    schema = None
    index_dumper = None

    # links configuration
    links_item = {
        "self": Link("{+api}/users/{id}"),
        "avatar": Link("{+api}/users/{id}/avatar.svg"),
    }
    links_search = pagination_links("{+api}/users{?args*}")

    components = [
        # order of components are important!
    ]
