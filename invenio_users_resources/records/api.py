# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-FileCopyrightText: 2022 CERN.
# SPDX-FileCopyrightText: 2024 Graz University of Technology.
# SPDX-FileCopyrightText: 2024 Ubiquity Press.
# SPDX-FileCopyrightText: 2025-2026 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT

"""API classes for user and group management in Invenio."""

import unicodedata
from collections import namedtuple
from datetime import datetime

from flask import current_app
from invenio_access import ActionRoles, superuser_access
from invenio_accounts.models import Domain, User
from invenio_accounts.proxies import current_datastore
from invenio_db import db
from invenio_i18n import gettext as _
from invenio_records.dumpers import SearchDumper, SearchDumperExt
from invenio_records.dumpers.indexedat import IndexedAtDumperExt
from invenio_records.systemfields import ModelField
from invenio_records_resources.records.api import Record
from invenio_records_resources.records.systemfields import IndexField
from marshmallow import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.exc import NoResultFound

from .dumpers import EmailFieldDumperExt
from .models import DomainAggregateModel, GroupAggregateModel, UserAggregateModel
from .systemfields import (
    AccountStatusField,
    AccountVisibilityField,
    DomainCategoryNameField,
    DomainField,
    DomainOrgField,
    DomainStatusNameField,
    IsNotNoneField,
    UserIdentitiesField,
    UserRolesField,
)

EmulatedPID = namedtuple("EmulatedPID", ["pid_value"])
"""Emulated PID"""


class AggregatePID:
    """Helper emulate a PID field."""

    def __init__(self, pid_field):
        """Constructor."""
        self._pid_field = pid_field

    def __get__(self, record, owner=None):
        """Evaluate the property."""
        if record is None:
            return GetRecordResolver(owner)
        return EmulatedPID(record[self._pid_field])


class GetRecordResolver(object):
    """Resolver that simply uses get record."""

    def __init__(self, record_cls):
        """Initialize resolver."""
        self._record_cls = record_cls

    def resolve(self, pid_value):
        """Simply get the record."""
        return self._record_cls.get_record(pid_value)


class BaseAggregate(Record):
    """An aggregate of information about a user group/role."""

    metadata = None
    """Disabled metadata field from the base class."""

    def __getitem__(self, name):
        """Get a dict key item."""
        try:
            return getattr(self.model, name)
        except AttributeError:
            raise KeyError(name)

    def __repr__(self):
        """Create string representation."""
        return f"<{self.__class__.__name__}: {self.model.data}>"

    def __unicode__(self):
        """Create string representation."""
        return self.__repr__()

    @classmethod
    def from_model(cls, sa_model):
        """Create an aggregate from an SQL Alchemy model."""
        return cls({}, model=cls.model_cls(model_obj=sa_model))

    def _validate(self, *args, **kwargs):
        """Skip the validation."""
        pass

    def commit(self):
        """Update the aggregate data on commit."""
        # You can only commit if you have an underlying model object.
        if self.model._model_obj is None:
            raise ValueError(f"{self.__class__.__name__} not backed by a model.")
        if self.model._model_obj not in db.session:
            with db.session.begin_nested():
                # make sure we get an id assigned
                db.session.add(self.model._model_obj)
        # Basically re-parses the model object.
        model = self.model_cls(model_obj=self.model._model_obj)
        self.model = model
        return self


def _validate_user_data(user_data):
    """Validate the entered data for the user creation.

    This is a special case for validation done outside of the schema because it requires
    database queries that can significantly slow down serialization. We want to perform
    this validation upon account creation.
    Also, we can't let this fail naturaly at the DB level because it will happen during the
    `commit` state of the UOW and the feedback to the form can't be sent.
    """
    errors = {}
    username = user_data.get("username")
    email = user_data["email"]
    # Check if Email exists already
    existing_email = db.session.query(User).filter_by(email=email).first()
    if existing_email:
        errors["email"] = [_("Email already used by another account.")]
    # Check if Username exists already
    if username is not None:
        existing_username = db.session.query(User).filter_by(username=username).first()
        if existing_username:
            errors["username"] = [_("Username already used by another account.")]
    if errors:
        raise ValidationError(errors)


def _validate_group_data(data):
    """Validate the group data."""
    name = data.get("name")
    if not name:
        return

    errors = {}
    stmt = select(current_datastore.role_model.id).where(
        current_datastore.role_model.name == name
    )
    existing_role_id = db.session.execute(stmt).scalar_one_or_none()

    if existing_role_id:
        errors["name"] = [_("Role name already used by another group.")]
    if errors:
        raise ValidationError(errors)


class UserAggregate(BaseAggregate):
    """An aggregate of information about a user."""

    model_cls = UserAggregateModel
    """The model class for the request."""

    # NOTE: the "uuid" isn't a UUID but contains the same value as the "id"
    #       field, which is currently an integer for User objects!
    dumper = SearchDumper(
        extensions=[
            EmailFieldDumperExt("email"),
            IndexedAtDumperExt(),
        ],
        model_fields={
            "id": ("uuid", int),
        },
    )
    """Search dumper with configured extensions."""

    index = IndexField("users-user-v3.0.0", search_alias="users")
    """The search engine index to use."""

    id = ModelField("id", dump_type=int)
    """The user identifier."""

    active = ModelField("active", dump_type=bool)
    """Determine is user is active and can login."""

    # Profile fields
    username = ModelField("username", dump_type=str)
    """The user's email address."""

    email = ModelField("email", dump_type=str)
    """The user's email address."""

    domain = ModelField("domain", dump_type=str)
    """The domain of the users' email address."""

    profile = ModelField("profile", dump_type=dict)
    """The user's profile."""

    preferences = ModelField("preferences", dump_type=dict)
    """User preferences."""

    # Timestamps fields
    confirmed_at = ModelField("confirmed_at", dump_type=datetime)
    """Timestamp for when account was confirmed."""

    verified_at = ModelField("verified_at", dump_type=datetime)
    """Timestamp for when account was verified."""

    blocked_at = ModelField("blocked_at", dump_type=datetime)
    """Timestamp for when account was blocked."""

    current_login_at = ModelField("current_login_at", dump_type=datetime)
    """Timestamp for when account was blocked."""

    last_login_at = ModelField("last_login_at", dump_type=datetime)
    """Timestamp for last login."""

    last_login_ip = ModelField("last_login_ip", dump_type=str)
    """IP address of last login."""

    current_login_ip = ModelField("current_login_ip", dump_type=str)
    """IP address of current login."""

    login_count = ModelField("login_count", dump_type=int)
    """Number of times the user has logged in."""

    confirmed = IsNotNoneField("confirmed_at", index=True)
    """Boolean to determine if verified."""

    verified = IsNotNoneField("verified_at", index=True)
    """Boolean to determine if verified."""

    blocked = IsNotNoneField("blocked_at", index=True)
    """Boolean to determine if verified."""

    # Status fields
    status = AccountStatusField(index=True)
    """Combined account status attribute."""

    visibility = AccountVisibilityField(index=True)
    """Combined profile visibility attribute."""

    domaininfo = DomainField(use_cache=True, index=True)
    """Domain information."""

    identities = UserIdentitiesField("identities", use_cache=True, index=True)
    """User identities."""

    roles = UserRolesField("roles", index=True)
    """User role names."""

    @property
    def avatar_chars(self):
        """Get avatar characters for user."""
        text = None
        if self.profile.get("full_name"):
            text = self.profile["full_name"]
        elif self.username:
            text = self.username
        else:
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVXYZ"
            text = alphabet[self.id % len(alphabet)]

        return text[0].upper()

    @property
    def avatar_color(self):
        """Get avatar color for user."""
        colors = current_app.config["USERS_RESOURCES_AVATAR_COLORS"]
        return colors[self.id % len(colors)]

    @classmethod
    def create(cls, data, id_=None, validator=None, format_checker=None, **kwargs):
        """Create a new User and store it in the database."""
        try:
            # Check if email and  username already exists by another account.
            _validate_user_data(data)
            # Create User
            account_user = current_datastore.create_user(**data)
            return cls.from_model(account_user)
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(message=f"Unexpected Issue: {str(e)}", data=data)

    def verify(self):
        """Activates the current user.

        Activation of the user is proxied through the datastore.
        """
        user = self.model.model_obj
        if user is None:
            return False
        return current_datastore.verify_user(user)

    def block(self):
        """Blocks a user."""
        user = self.model.model_obj
        if user is None:
            return False
        return current_datastore.block_user(user)

    def activate(self):
        """Activate a previously deactivated user."""
        user = self.model.model_obj
        if user is None:
            return False
        return current_datastore.activate_user(user)

    def deactivate(self):
        """Deactivates the current user."""
        user = self.model.model_obj
        if user is None:
            return False
        return current_datastore.deactivate_user(user)

    def get_groups(self):
        """Return assigned group role model objects."""
        return sorted(self.model.model_obj.roles, key=lambda role: role.name)

    def group_ids(self):
        """Return assigned group IDs."""
        return [str(group.id) for group in self.get_groups()]

    def add_group(self, group_id):
        """Add group membership to user if not already assigned."""
        self.add_groups([group_id])
        return self

    def remove_group(self, group_id):
        """Remove group membership from user if assigned."""
        self.remove_groups([group_id])
        return self

    def _resolve_groups_to_roles(self, group_ids):
        """Resolve group identifiers (ID or name) to role model objects."""
        normalized_group_ids = []
        for group_id in group_ids:
            normalized = str(group_id).strip()
            if normalized and normalized not in normalized_group_ids:
                normalized_group_ids.append(normalized)

        if not normalized_group_ids:
            return []

        role_model = current_datastore.role_model
        group_roles = (
            db.session.query(role_model)
            .filter(
                or_(
                    role_model.id.in_(normalized_group_ids),
                    role_model.name.in_(normalized_group_ids),
                )
            )
            .all()
        )
        group_roles_by_id = {
            str(group_role.id): group_role for group_role in group_roles
        }
        group_roles_by_name = {
            str(group_role.name): group_role for group_role in group_roles
        }

        resolved_group_roles = []
        seen_group_role_ids = set()
        for group_id in normalized_group_ids:
            group_role = group_roles_by_id.get(group_id) or group_roles_by_name.get(
                group_id
            )
            if group_role is None:
                raise ValidationError({"groups": [_("Group does not exist.")]})
            group_role_id = str(group_role.id)
            if group_role_id in seen_group_role_ids:
                continue
            seen_group_role_ids.add(group_role_id)
            resolved_group_roles.append(group_role)
        return resolved_group_roles

    def resolve_group_ids(self, group_ids, require=False):
        """Resolve group identifiers (ID or name) to canonical group IDs."""
        resolved_group_ids = [
            str(role.id) for role in self._resolve_groups_to_roles(group_ids)
        ]
        if require and not resolved_group_ids:
            raise ValidationError({"groups": [_("Group ID cannot be empty.")]})
        return resolved_group_ids

    def add_groups(self, group_ids):
        """Add multiple group memberships to user if not already assigned."""
        user = self.model.model_obj

        added = []
        for group_role in self._resolve_groups_to_roles(group_ids):
            if current_datastore.add_role_to_user(user, group_role):
                added.append(str(group_role.id))

        return {
            "added": sorted(added),
            "removed": [],
            "groups": self.group_ids(),
        }

    def remove_groups(self, group_ids):
        """Remove multiple group memberships from user if assigned."""
        user = self.model.model_obj

        removed = []
        for group_role in self._resolve_groups_to_roles(group_ids):
            if current_datastore.remove_role_from_user(user, group_role):
                removed.append(str(group_role.id))

        return {
            "added": [],
            "removed": sorted(removed),
            "groups": self.group_ids(),
        }

    def set_groups(self, group_ids):
        """Replace group memberships for a user."""
        requested_groups = self._resolve_groups_to_roles(group_ids)
        requested_group_ids = {str(group.id) for group in requested_groups}
        current_group_ids = set(self.group_ids())

        to_add = requested_group_ids - current_group_ids
        to_remove = current_group_ids - requested_group_ids

        self.add_groups(to_add)
        self.remove_groups(to_remove)

        return {
            "added": sorted(to_add),
            "removed": sorted(to_remove),
            "groups": self.group_ids(),
        }

    @classmethod
    def get_record(cls, id_):
        """Get the user via the specified ID."""
        with db.session.no_autoflush:
            # Notifications builders right now manage to pass "system" as an
            # id when they try use the ServiceResultResolvers on
            # {'user': 'system'} which results in a database transaction being
            # rolled back when quering on an integer id column with a string.
            if id_ == "system":
                return None

            user = current_datastore.get_user_by_id(id_)
        if user is None:
            return None

        with db.session.no_autoflush:
            return cls.from_model(user)


class GroupAggregate(BaseAggregate):
    """An aggregate of information about a user group/role."""

    model_cls = GroupAggregateModel
    """The model class for the user group aggregate."""

    # NOTE: Role identifiers intentionally mirror role names. Permission checks
    #       use the id field, while configuration stays human-readable.
    dumper = SearchDumper(extensions=[], model_fields={"id": ("uuid", str)})
    """Search index dumper."""

    index = IndexField("groups-group-v2.0.0", search_alias="groups")
    """The search engine index to use."""

    id = ModelField("id", dump_type=str)
    """ID of group."""

    name = ModelField("name", dump_type=str)
    """The group's name."""

    description = ModelField("description", dump_type=str)
    """The group's description."""

    is_managed = ModelField("is_managed", dump_type=bool)
    """If the group is managed manually."""

    @property
    def avatar_chars(self):
        """Get avatar characters for user."""
        return self.id[0].upper()

    @property
    def avatar_color(self):
        """Get avatar color for user."""
        colors = current_app.config["USERS_RESOURCES_AVATAR_COLORS"]
        normalized_group_initial = unicodedata.normalize("NFKD", self.id[0]).encode(
            "ascii", "ignore"
        )
        return colors[int(normalized_group_initial, base=36) % len(colors)]

    @property
    def revision_id(self):
        """Return a revision id suitable for search engine versioning.

        We offset the SQLAlchemy ``version_id`` by 1 so that recreated roles
        (same id/name) always index with a version >= any previous document in
        the search index, avoiding version conflicts during reindexing. We also
        fall back to the ``updated`` timestamp to produce a larger, monotonic
        value when the DB ``version_id`` is low (e.g., after a recreate).
        """
        if not self.model:
            return 1

        version = self.model.version_id or 0
        updated_ts = int(self.model.updated.timestamp()) if self.model.updated else 0
        return max(version + 1, updated_ts)

    @classmethod
    def superadmin_group_ids(cls):
        """Return group IDs that grant superuser access."""
        return {
            str(action_role.role_id)
            for action_role in ActionRoles.query_by_action(superuser_access).all()
        }

    @classmethod
    def available_groups(cls, exclude_group_ids=None):
        """Return groups available for assignment."""
        role_model = current_datastore.role_model
        query = db.session.query(role_model).order_by(role_model.name)
        if exclude_group_ids:
            query = query.filter(role_model.id.notin_(exclude_group_ids))
        return query.all()

    @classmethod
    def get_record(cls, id_):
        """Get the user group via the specified ID."""
        # TODO how do we want to resolve the roles? via ID or name?
        with db.session.no_autoflush:
            role = db.session.get(current_datastore.role_model, id_)
            if role is None:
                return None
            return cls.from_model(role)

    @classmethod
    def get_record_by_name(cls, name):
        """Get the user group via the specified ID."""
        # TODO how do we want to resolve the roles? via ID or name?
        with db.session.no_autoflush:
            role = (
                db.session.query(current_datastore.role_model)
                .filter_by(name=name)
                .one_or_none()
            )
            if role is None:
                return None
            return cls.from_model(role)

    @classmethod
    def create(cls, data):
        """Create a new group/role and store it in the database."""
        role_data = {
            "id": data["name"],
            "name": data["name"],
            "description": data.get("description"),
        }

        _validate_group_data(role_data)
        role = current_datastore.create_role(**role_data)
        return cls.from_model(role)

    def update(self, data, id_):
        """Update the group/role attributes.

        Update is proxied through direct attribute modification.
        """
        role = self.model.model_obj
        if role is None:
            role = db.session.get(current_datastore.role_model, id_)

        data.pop("name", None)
        role.description = data.get("description", role.description)
        role = current_datastore.update_role(role)
        return self.from_model(role)

    def delete(self):
        """Delete the group/role.

        Deletion is proxied through the datastore.
        """
        role = self.model.model_obj
        if role is None:
            raise ValueError("Cannot delete group without an underlying model.")
        current_datastore.delete(role)


class OrgNameDumperExt(SearchDumperExt):
    """Custom fields dumper extension."""

    def dump(self, record, data):
        """Dump for faceting."""
        org = data.get("org", None)
        if org and len(org) > 0:
            data["org_names"] = [o["name"] for o in org]

    def load(self, data, record_cls):
        """Remove data from object."""
        data.pop("org_names", None)


class DomainAggregate(BaseAggregate):
    """An aggregate of information about a user."""

    model_cls = DomainAggregateModel
    """The model class for the request."""

    # NOTE: the "uuid" isn't a UUID but contains the same value as the "id"
    #       field, which is currently an integer for User objects!
    dumper = SearchDumper(
        extensions=[
            IndexedAtDumperExt(),
            OrgNameDumperExt(),
        ],
        model_fields={
            "id": ("uuid", int),
        },
    )
    """Search dumper with configured extensions."""

    index = IndexField("domains-domain-v1.0.0", search_alias="domains")
    """The search engine index to use."""

    pid = AggregatePID("domain")
    """Needed to emulate pid access."""

    id = ModelField("id", dump_type=int)
    """The user identifier."""

    domain = ModelField("domain", dump_type=str)
    """The domain of the users' email address."""

    tld = ModelField("tld", dump_type=str)
    """Top level domain."""

    status = ModelField("status", dump_type=int)
    """Domain status."""

    status_name = DomainStatusNameField(index=True)
    """Domain status name."""

    flagged = ModelField("flagged", dump_type=bool)
    """Flagged."""

    flagged_source = ModelField("flagged_source", dump_type=str)
    """Source of flagging."""

    category = ModelField("category", dump_type=int)
    """Domain category."""

    category_name = DomainCategoryNameField(use_cache=True, index=True)
    """Domain category name."""

    org_id = ModelField("org_id", dump_type=int)
    """Number of users."""

    org = DomainOrgField("org", use_cache=True, index=True)
    """Organization behind the domain."""

    num_users = ModelField("num_users", dump_type=int)
    """Number of users."""

    num_active = ModelField("num_active", dump_type=int)
    """Number of active users."""

    num_inactive = ModelField("num_inactive", dump_type=int)
    """Number of inactive users."""

    num_confirmed = ModelField("num_confirmed", dump_type=int)
    """Number of confirmed users."""

    num_verified = ModelField("num_verified", dump_type=int)
    """Number of verified users."""

    num_blocked = ModelField("num_blocked", dump_type=int)
    """Number of blocked users."""

    @classmethod
    def get_record(cls, id_):
        """Get the user via the specified ID."""
        with db.session.no_autoflush:
            domain = current_datastore.find_domain(id_)
        if domain is None:
            raise NoResultFound()
        return cls.from_model(domain)

    @classmethod
    def create(cls, data, id_=None, **kwargs):
        """Create a domain."""
        return DomainAggregate(data, model=DomainAggregateModel(model_obj=Domain()))

    def delete(self, force=True):
        """Delete the domain."""
        db.session.delete(self.model.model_obj)
