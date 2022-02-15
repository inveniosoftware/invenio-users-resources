# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 TU Wien.
# Copyright (C) 2022 European Union.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Users service."""

from invenio_accounts.models import User
from invenio_records_resources.services import RecordService
from invenio_records_resources.services.uow import RecordCommitOp, unit_of_work

from ...records.api import UserAggregate

from invenio_userprofiles.models import UserProfile
from flask import send_file as _send_file
from flask import render_template, request
import re
from io import BytesIO

user_colors = ['#e06055', '#ff8a65', '#e91e63', '#f06292', '#673ab7', '#ba68c8', '#7986cb', '#3f51b5', '#5e97f6',
               '#00a4e4', '#4dd0e1', '#0097a7', '#d4e157', '#aed581', '#57bb8a', '#4db6ac', '#607d8b', '#795548',
               '#a1887f', '#fdd835', '#a3a3a3', '#556c60', '#605264', '#923035', '#915a30', '#55526f', '#67635a']


class UsersService(RecordService):
    """Users service."""

    @property
    def user_cls(self):
        """Alias for record_cls."""
        return self.record_cls

    @unit_of_work()
    def create(self, identity, data, raise_errors=True, uow=None):
        """Create a user."""
        self.require_permission(identity, "create")

        # validate data
        data, errors = self.schema.load(
            data,
            context={"identity": identity},
        )

        # create the user with the specified data
        user = self.user_cls.create(data)

        # run components
        self.run_components(
            "create",
            identity,
            data=data,
            user=user,
            errors=errors,
            uow=uow,
        )

        # persist user (DB and index)
        uow.register(RecordCommitOp(user, self.indexer))

        return self.result_item(
            self, identity, user, links_tpl=self.links_item_tpl, errors=errors
        )

    def read(self, identity, id_):
        """Retrieve a user."""
        # resolve and require permission
        user = UserAggregate.get_record(id_)
        if user is None:
            raise LookupError(f"No user with id '{id_}'.")

        self.require_permission(identity, "read", user=user)

        # run components
        for component in self.components:
            if hasattr(component, "read"):
                component.read(identity, user=user)

        return self.result_item(
            self, identity, user, links_tpl=self.links_item_tpl
        )

    def get_avatar(self, identity, id_):
        """Get a user's avatar."""

        # user = self.read(identity, id)
        name = UserProfile.get_by_userid(id_).username
        # email = UserProfile.get_by_userid(id_).email
        text = name[0].upper()
        color = self.get_color_for_user_id(id_)
        avatar = render_template('avatarc.svg', bg_color=color, text=text)
        return self.send_file('avatar.svg', BytesIO(avatar.encode()), mimetype='image/svg+xml',
                              no_cache=False, inline=True, safe=False, max_age=86400 * 7)

    def get_color_for_user_id(self, id):
        """Calculate a unique color for a user based on their id.
        :param user_id: the user ID (int), or otherwise a string (external search results)
        """
        return user_colors[id % len(user_colors)]

    def send_file(self, name, path_or_fd, mimetype, last_modified=None, no_cache=True, inline=None, conditional=False,
                  safe=True,
                  **kwargs):
        """Send a file to the user.
        `name` is required and should be the filename visible to the user.
        `path_or_fd` is either the physical path to the file or a file-like object (e.g. a StringIO).
        `mimetype` SHOULD be a proper MIME type such as image/png. It may also be an indico-style file type such as JPG.
        `last_modified` may contain a unix timestamp or datetime object indicating the last modification of the file.
        `no_cache` can be set to False to disable no-cache headers. Setting `conditional` to `True` overrides it (`False`).
        `inline` defaults to true except for certain filetypes like XML and CSV. It SHOULD be set to false only when you
        want to force the user's browser to download the file. Usually it is much nicer if e.g. a PDF file can be displayed
        inline so don't disable it unless really necessary.
        `conditional` is very useful when sending static files such as CSS/JS/images. It will allow the browser to retrieve
        the file only if it has been modified (based on mtime and size). Setting it will override `no_cache`.
        `safe` adds some basic security features such a adding a content-security-policy and forcing inline=False for
        text/html mimetypes
        """

        name = re.sub(r'\s+', ' ', name).strip()  # get rid of crap like linebreaks
        assert '/' in mimetype
        if inline is None:
            inline = mimetype not in ('text/csv', 'text/xml', 'application/xml')
        if request.user_agent.platform == 'Android':
            # Android is just full of fail when it comes to inline content-disposition...
            inline = False
        # if _is_office_mimetype(mimetype):
        #    inline = False
        if safe and mimetype in ('text/html', 'image/svg+xml'):
            inline = False
        try:
            rv = _send_file(path_or_fd, mimetype=mimetype, as_attachment=(not inline), download_name=name,
                            conditional=conditional, last_modified=last_modified, **kwargs)
        except OSError:
            raise OSError
            # if not current_app.debug:
            #    raise
            # raise NotFound('File not found: %s' % path_or_fd)
        if safe:
            rv.headers.add('Content-Security-Policy', "script-src 'self'; object-src 'self'")
        # if the request is conditional, then caching shouldn't be disabled
        if not conditional and no_cache:
            del rv.expires
            del rv.cache_control.max_age
            rv.cache_control.public = False
            rv.cache_control.private = True
            rv.cache_control.no_cache = True

        return rv

    def rebuild_index(self, identity, uow=None):
        """Reindex all users managed by this service."""
        for user in User.query.all():
            user_agg = self.record_cls.from_user(user)
            self.indexer.index(user_agg)

        return True
