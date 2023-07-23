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
from invenio_access.permissions import system_process, system_user_id
from invenio_accounts.models import User
from invenio_records_resources.references.entity_resolvers import (
    EntityProxy,
    EntityResolver,
)
from sqlalchemy.exc import NoResultFound

from .proxies import current_users_service
from .services.schemas import SystemUserSchema, UserGhostSchema, UserSchema
from .services.users.config import UsersServiceConfig
from .permissions import user_moderation_action


class UserProxy(EntityProxy):
    """Resolver proxy for a User entity."""

    def _resolve(self):
        """Resolve the User from the proxy's reference dict, or system_identity."""
        user_id = self._parse_ref_dict_id()
        if user_id == system_user_id:  # system_user_id is a string: "system"
            return self.system_record()
        else:
            try:
                return User.query.get(int(user_id))
            except NoResultFound:
                return self.ghost_record({"id": user_id})

    def get_needs(self, ctx=None):
        """Get the UserNeed for the referenced user."""
        user_id = self._parse_ref_dict_id()
        if user_id == system_user_id:
            return [system_process]
        else:
            return [UserNeed(int(user_id))]

    def ghost_record(self, value):
        """Return default representation of not resolved user."""
        return UserGhostSchema().dump(value)

    def system_record(self):
        """Return the representation of system user."""
        default_constant_values = {}
        return SystemUserSchema().dump(default_constant_values)

    def pick_resolved_fields(self, identity, resolved_dict):
        """Select which fields to return when resolving the reference."""
        profile = resolved_dict.get("profile", {})
        fake_user_obj = SimpleNamespace(id=resolved_dict["id"])
        avatar = current_users_service.links_item_tpl.expand(identity, fake_user_obj)[
            "avatar"
        ]
        serialized_user = {
            "id": resolved_dict["id"],
            "username": resolved_dict.get("username", ""),
            "email": resolved_dict.get("email", ""),
            "profile": {
                "full_name": profile.get("full_name", ""),
                "affiliations": profile.get("affiliations", ""),
            },
            "links": {"avatar": avatar},
        }

        return serialized_user


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


class UserModerationProxy(UserProxy):
    """Resolver proxy for a User Moderation entity."""

    def get_needs(self, ctx=None):
        """Return user moderaction action need."""
        # System process need is also valid for UserModeration actions
        return [user_moderation_action, system_process]


class UserModerationResolver(UserResolver):
    """User moderation entity resolver.

    The entity resolver enables Invenio-Requests to understand moderators as
    receiver, as well as system process, enabling actions on requests.
    """

    type_id = "user_moderation"
    """Type identifier for this resolver."""

    def _reference_entity(self, entity):
        """Create a reference dict for the given user."""
        return {"user_moderation": str(entity.id)}

    def _get_entity_proxy(self, ref_dict):
        """Return a UserModerationProxy for the given reference dict."""
        return UserModerationProxy(self, ref_dict)
