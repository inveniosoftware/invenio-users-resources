# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Results for the user groups service."""

from invenio_records_resources.services.records.results import RecordItem, RecordList


class GroupItem(RecordItem):
    """Single user group result."""

    def __init__(
        self,
        service,
        identity,
        group,
        errors=None,
        links_tpl=None,
        schema=None,
        **kwargs,
    ):
        """Constructor."""
        self._data = None
        self._errors = errors
        self._identity = identity
        self._group = group
        self._service = service
        self._links_tpl = links_tpl
        self._schema = schema or service.schema

    @property
    def id(self):
        """Identity of the user group."""
        return str(self._group.id)

    def __getitem__(self, key):
        """Key a key from the data."""
        return self.data[key]

    @property
    def links(self):
        """Get links for this result item."""
        return self._links_tpl.expand(self._identity, self._group)

    @property
    def _obj(self):
        """Return the object to dump."""
        return self._group

    @property
    def data(self):
        """Property to get the user group."""
        if self._data:
            return self._data

        self._data = self._schema.dump(
            self._obj,
            context={
                "identity": self._identity,
                "record": self._group,
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
        """Get a dictionary for the user group."""
        res = self.data
        if self._errors:
            res["errors"] = self._errors
        return res


class GroupList(RecordList):
    """List of user group results."""

    @property
    def hits(self):
        """Iterator over the hits."""
        group_cls = self._service.record_cls

        for hit in self._results:
            # load dump
            group = group_cls.loads(hit.to_dict())
            schema = self._service.schema

            # project the user group
            projection = schema.dump(
                group,
                context={
                    "identity": self._identity,
                    "record": group,
                },
            )

            # inject the links
            if self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(self._identity, group)

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
