# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Results for the users service."""

from invenio_records_resources.services.records.results import RecordItem, RecordList


def _role_names(user):
    """Return list of role names."""
    model = getattr(user, "model", user)
    model_obj = getattr(model, "_model_obj", model)

    if not hasattr(model_obj, "roles"):
        model_obj = user

    roles = getattr(model_obj, "roles", None)
    if not roles:
        return []

    return [role.name for role in roles]


def _can_manage_groups(identity, service):
    """Return True if the identity can manage groups."""
    policy = service.config.permission_policy_cls
    permission = policy(action="manage_groups", identity=identity)
    return permission.allows(identity)


def _apply_roles(payload, roles, has_permission):
    """Populate flat/profile role projections."""
    if has_permission:
        # Admin responses expose the same roles list both at the top level
        # and inside the profile projection, so we set both here.
        payload["roles"] = ", ".join(roles) if roles else ""
        profile = dict(payload.get("profile") or {})
        profile["roles"] = ", ".join(roles) if roles else ""
        payload["profile"] = profile

    return payload


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
        roles = _role_names(self._user)
        has_permission = _can_manage_groups(self._identity, self._service)
        _apply_roles(self._data, roles, has_permission)

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
        has_permission = _can_manage_groups(self._identity, self._service)

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

            roles = _role_names(user)
            _apply_roles(projection, roles, has_permission)

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
