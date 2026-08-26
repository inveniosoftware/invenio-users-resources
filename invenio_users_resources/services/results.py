# SPDX-FileCopyrightText: 2022 CERN.
# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Avatar results for users and groups."""

import hashlib
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
    def etag(self) -> str:
        """Get an ETag for the avatar."""
        return hashlib.sha256(
            f"{self._obj.avatar_chars}{self._obj.avatar_color}".encode("utf-8")
        ).hexdigest()[:12]

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
