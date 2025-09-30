# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2025 Graz University of Technology.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Avatar results for users and groups."""

import unicodedata
from datetime import datetime, timedelta, timezone
from io import BytesIO

from flask import render_template


class AvatarResult:
    """An avatar result for a user or group."""

    def __init__(
        self,
        user_or_group,
    ):
        """Constructor."""
        self._obj = user_or_group

    @property
    def bytes_io(self):
        """Get the avatar image file."""
        return BytesIO(
            render_template(
                "avatar.svg",
                bg_color=self._obj.avatar_color,
                text=self._obj.avatar_chars,
            ).encode("utf8")
        )

    @property
    def mimetype(self):
        """Get the MIME type."""
        return "image/svg+xml"

    @property
    def name(self):
        """Get the filename of the avatar."""
        return "avatar.svg"

    @property
    def etag(self):
        """Get an ETag for the avatar."""
        # etags must be ascii. If the avatar_chars are not ascii, we need to
        # normalize them to ascii. This is done by removing accents and
        # diacritics from the characters.
        etag_start = self._obj.avatar_chars
        if not all(ord(c) < 128 for c in etag_start):
            etag_start = "".join(
                c
                for c in unicodedata.normalize("NFD", etag_start)
                if unicodedata.category(c) != "Mn"
            )
        return f"{etag_start}{self._obj.avatar_color}"

    @property
    def last_modified(self):
        """Get last modified date for the response."""
        max_age = datetime.now(timezone.utc) - timedelta(days=7)
        return self._obj.updated if self._obj.updated > max_age else max_age

    @property
    def max_age(self):
        """Get time out duration for cached avatars in seconds."""
        # As avatars are often called it should be cached to reduce the load on the user
        # currently set to 5 minutes as a reasonable time
        return 60 * 5
