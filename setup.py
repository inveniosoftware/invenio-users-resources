# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio module providing management APIs for users and roles/groups."""

import os

from setuptools import find_packages, setup

readme = open("README.rst").read()
history = open("CHANGES.rst").read()

records_resources_version = ">=0.18.3,<0.19"

tests_require = [
    "pytest-invenio>=1.4.0",
]

extras_require = {
    "docs": [
        "Sphinx>=4.2.0",
    ],
    "elasticsearch6": [
        f"invenio-records-resources[elasticsearch6]{records_resources_version}"
    ],
    "elasticsearch7": [
        f"invenio-records-resources[elasticsearch7]{records_resources_version}"
    ],
    "mysql": [f"invenio-records-resources[mysql]{records_resources_version}"],
    "postgresql": [f"invenio-records-resources[postgresql]{records_resources_version}"],
    "sqlite": [f"invenio-records-resources[sqlite]{records_resources_version}"],
    "tests": tests_require,
}

extras_require["all"] = []
for name, reqs in extras_require.items():
    if name in (
        "elasticsearch6",
        "elasticsearch7",
        "mysql",
        "postgresql",
        "sqlite",
    ):
        continue
    extras_require["all"].extend(reqs)

setup_requires = [
    "Babel>=2.8",
]

install_requires = [
    "invenio-accounts>=2.0.0dev0",
    "invenio-i18n>=1.3.1",
    "invenio-userprofiles>=1.2.4",
    "invenio-oauthclient>=1.5.4",
    f"invenio-records-resources{records_resources_version}",
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join("invenio_users_resources", "version.py"), "rt") as fp:
    exec(fp.read(), g)
    version = g["__version__"]

setup(
    name="invenio-users-resources",
    version=version,
    description=__doc__,
    long_description=readme + "\n\n" + history,
    keywords="invenio users roles groups management",
    license="MIT",
    author="CERN",
    author_email="info@inveniosoftware.org",
    url="https://github.com/inveniosoftware/invenio-users-resources",
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    entry_points={
        "invenio_base.apps": [
            "invenio_users_resources = invenio_users_resources:InvenioUsersResources",  # noqa
        ],
        "invenio_base.api_apps": [
            "invenio_users_resources = invenio_users_resources:InvenioUsersResources",  # noqa
        ],
        "invenio_base.api_blueprints": [
            "invenio_users = invenio_users_resources.views:create_users_resources_bp",  # noqa
            "invenio_groups = invenio_users_resources.views:create_groups_resources_bp",  # noqa
        ],
        "invenio_search.mappings": [
            "users = invenio_users_resources.records.mappings",
            "groups = invenio_users_resources.records.mappings",
        ],
        "invenio_i18n.translations": [
            "messages = invenio_users_resources",
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Development Status :: 1 - Planning",
    ],
)
