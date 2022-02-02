# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 European Union.
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Avatar tests."""


def test_user_avatar(client, user1):
    res = client.get(f"/users/{user1.id}/avatar.svg")
    assert res.status_code == 200
    assert res.mimetype == "image/svg+xml"
    data = res.get_data()


def test_group_avatar(client, group):
    res = client.get(f"/groups/{group.id}/avatar.svg")
    assert res.status_code == 200
    assert res.mimetype == "image/svg+xml"
    data = res.get_data()

# TODO: test conditional requests
# TODO: test caching headers
# TODO: test invalid identifiers
