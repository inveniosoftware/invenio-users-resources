# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Results for the users service."""

from invenio_records_resources.services.records.results import RecordItem, RecordList


class UserItem(RecordItem):
    """Single user result."""

    def __init__(
        self,
        service,
        identity,
        user,
        errors=None,
        links_tpl=None,
        schema=None,
        **kwargs,
    ):
        """Constructor."""
        self._data = None
        self._errors = errors
        self._identity = identity
        self._user = user
        self._service = service
        self._links_tpl = links_tpl
        self._schema = schema or service.schema

    @property
    def id(self):
        """Identity of the user."""
        return str(self._user.id)

    def __getitem__(self, key):
        """Key a key from the data."""
        return self.data[key]

    @property
    def links(self):
        """Get links for this result item."""
        return self._links_tpl.expand(self._identity, self._user)

    @property
    def _obj(self):
        """Return the object to dump."""
        return self._user

    @property
    def data(self):
        """Property to get the user."""
        if self._data:
            return self._data

        self._data = self._schema.dump(
            self._obj,
            context={
                "identity": self._identity,
                "record": self._user,
            },
        )

        if self._links_tpl:
            self._data["links"] = self.links

        return self._data

    @property
    def errors(self):
        """Get the errors."""
        return self._errors

    def to_dict(self):
        """Get a dictionary for the user."""
        res = self.data
        if self._errors:
            res["errors"] = self._errors
        return res


class UserList(RecordList):
    """List of user results."""

    @property
    def hits(self):
        """Iterator over the hits."""
        user_cls = self._service.record_cls

        for hit in self._results:
            # load dump
            user = user_cls.loads(hit.to_dict())
            schema = self._service.schema

            # project the user
            projection = schema.dump(
                user,
                context={
                    "identity": self._identity,
                    "record": user,
                },
            )

            # inject the links
            if self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(self._identity, user)

            yield projection

    def to_dict(self):
        """Return result as a dictionary."""
        # TODO: This part should imitate the result item above. I.e. add a
        # "data" property which uses a ServiceSchema to dump the entire object.
        res = {
            "hits": {
                "hits": list(self.hits),
                "total": self.total,
            }
        }
        if self.aggregations:
            res["aggregations"] = self.aggregations

        if self._params:
            res["sortBy"] = self._params["sort"]
            if self._links_tpl:
                res["links"] = self._links_tpl.expand(self._identity, self.pagination)

        return res
