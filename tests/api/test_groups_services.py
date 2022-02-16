# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2021 CERN.
# Copyright (C) 2016-2021 European Union.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Users_resources tests."""

from invenio_users_resources.resources import UsersResource


def test_get_user_avatar(app, client, headers, example_group):
    group=example_group()
    res = client.get(f"/groups/{group.id}/avatar.svg")
    assert res.status_code == 200



