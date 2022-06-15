# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN
# Copyright (C) 2022 TU Wien.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Resolver and proxy for users."""

from types import SimpleNamespace

from flask_principal import UserNeed
from invenio_accounts.models import User
from invenio_records_resources.references.resolvers import EntityProxy, EntityResolver

from .proxies import current_users_service
from .services.users.config import UsersServiceConfig


class UserProxy(EntityProxy):
    """Resolver proxy for a User entity."""

    def _resolve(self):
        """Resolve the User from the proxy's reference dict."""
        user_id = int(self._parse_ref_dict_id())
        return User.query.get(user_id)

    def get_needs(self, ctx=None):
        """Get the UserNeed for the referenced user."""
        user_id = int(self._parse_ref_dict_id())
        return [UserNeed(user_id)]

    def pick_resolved_fields(self, resolved_dict):
        """Select which fields to return when resolving the reference."""
        profile = resolved_dict.get("profile", {})
        fake_user_obj = SimpleNamespace(id=resolved_dict["id"])
        avatar = current_users_service.links_item_tpl.expand(fake_user_obj)["avatar"]
        return {
            "id": resolved_dict["id"],
            "username": resolved_dict["username"],
            "email": resolved_dict.get("email", ""),
            "profile": {
                "full_name": profile.get("full_name", ""),
                "affiliations": profile.get("affiliations", ""),
            },
            "links": {"avatar": avatar},
        }


class UserResolver(EntityResolver):
    """Resolver for users."""

    type_id = "user"

    def __init__(self):
        """Constructor."""
        super().__init__(UsersServiceConfig.service_id)

    def matches_reference_dict(self, ref_dict):
        """Check if the reference dict references a user."""
        return self._parse_ref_dict_type(ref_dict) == self.type_id

    def _reference_entity(self, entity):
        """Create a reference dict for the given user."""
        return {"user": str(entity.id)}

    def matches_entity(self, entity):
        """Check if the entity is a user."""
        return isinstance(entity, User)

    def _get_entity_proxy(self, ref_dict):
        """Return a UserProxy for the given reference dict."""
        return UserProxy(self, ref_dict)
