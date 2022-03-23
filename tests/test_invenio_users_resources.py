# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from flask import Flask

from invenio_users_resources.ext import InvenioUsersResources


def test_version():
    """Test version import."""
    from invenio_users_resources import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = InvenioUsersResources(app)
    assert "invenio-users-resources" in app.extensions

    app = Flask("testapp")
    ext = InvenioUsersResources()
    assert "invenio-users-resources" not in app.extensions
    ext.init_app(app)
    assert "invenio-users-resources" in app.extensions
