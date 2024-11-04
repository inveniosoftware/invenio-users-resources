# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Resolver and proxy for users."""

from types import SimpleNamespace

from flask_principal import RoleNeed, UserNeed
from invenio_access.permissions import system_process, system_user_id
from invenio_accounts.models import Role, User
from invenio_db import db
from invenio_records_resources.references.entity_resolvers import (
    EntityProxy,
    EntityResolver,
)
from sqlalchemy.exc import NoResultFound

from .proxies import current_users_service
from .services.groups.config import GroupsServiceConfig
from .services.schemas import SystemUserSchema, UserGhostSchema
from .services.users.config import UsersServiceConfig


class UserProxy(EntityProxy):
    """Resolver proxy for a User entity."""

    def _resolve(self):
        """Resolve the User from the proxy's reference dict, or system_identity."""
        user_id = self._parse_ref_dict_id()
        if user_id == system_user_id:  # system_user_id is a string: "system"
            return self.system_record()
        else:
            try:
                return db.session.get(User, int(user_id))
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
        # TODO trying to recreate the user item here, there must be a better way!
        links = resolved_dict.get("links", {})
        links["avatar"] = avatar
        serialized_user = {
            "id": resolved_dict["id"],
            "username": resolved_dict.get("username", ""),
            "email": resolved_dict.get("email", ""),
            "profile": {
                "full_name": profile.get("full_name", ""),
                "affiliations": profile.get("affiliations", ""),
            },
            "links": links,
            "blocked_at": resolved_dict.get("blocked_at"),
            "verified_at": resolved_dict.get("verified_at"),
            "confirmed_at": resolved_dict.get("confirmed_at"),
            "active": resolved_dict.get("active"),
            "is_current_user": resolved_dict.get("is_current_user"),
        }

        return serialized_user


class UserResolver(EntityResolver):
    """Resolver for users."""

    type_id = "user"

    def __init__(self):
        """Constructor."""
        # There's a bit of a mixup of type_key and type_id. Base resolver has no
        # type_key, but RecordResolvers have.
        self.type_key = self.type_id
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


class GroupProxy(EntityProxy):
    """Resolver proxy for a Role entity."""

    def _resolve(self):
        """Resolve the User from the proxy's reference dict, or system_identity."""
        # Resolves to role name, not id
        role_id = self._parse_ref_dict_id()
        try:
            return (
                db.session.query(Role)
                .filter(Role.name == role_id)  # TODO to be changed to role id
                .one()
            )
        except NoResultFound:
            return {}

    def pick_resolved_fields(self, identity, resolved_dict):
        """Select which fields to return when resolving the reference."""
        serialized_role = {
            "id": resolved_dict.get("id", ""),
            "name": resolved_dict.get("name", ""),
        }

        return serialized_role

    def get_needs(self, ctx=None):
        """Return needs based on the given roles."""
        role_id = self._parse_ref_dict_id()
        return [RoleNeed(role_id)]

    def ghost_record(self, value):
        """Return default representation of not resolved group.

        .. note::

            Only groups that are not indexed should need this. Non-indexed groups include groups that were not created by users
            e.g. user-moderation.
        """
        return {}


class GroupResolver(EntityResolver):
    """Group entity resolver."""

    type_id = "group"
    """Type identifier for this resolver."""

    def __init__(self):
        """Constructor."""
        # There's a bit of a mixup of type_key and type_id. Base resolver has no
        # type_key, but RecordResolvers have.
        self.type_key = self.type_id
        super().__init__(GroupsServiceConfig.service_id)

    def matches_reference_dict(self, ref_dict):
        """Check if the reference dict references a role."""
        return self._parse_ref_dict_type(ref_dict) == self.type_id

    def _reference_entity(self, entity):
        """Create a reference dict for the given user."""
        return {"group": str(entity.id)}

    def matches_entity(self, entity):
        """Check if the entity is a Role."""
        return isinstance(entity, Role)

    def _get_entity_proxy(self, ref_dict):
        """Return a GroupProxy for the given reference dict."""
        return GroupProxy(self, ref_dict)
