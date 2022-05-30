# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Groups resource tests."""


def test_group_avatar(app, client, group, user_pub):
    res = client.get(f"/groups/{group.name}/avatar.svg")
    assert res.status_code == 403

    user_pub.login(client)

    res = client.get(f"/groups/{group.name}/avatar.svg")
    assert res.status_code == 200
    assert res.mimetype == "image/svg+xml"
    data = res.get_data()


# TODO: test conditional requests
# TODO: test caching headers
# TODO: test invalid identifiers
