from unittest.mock import Mock

import pytest

from invenio_users_resources.services.results import AvatarResult


@pytest.mark.parametrize(
    "avatar_chars,avatar_color",
    [
        ("Č", "#e06055"),
        ("Ł", "#ff8a65"),
        ("Đ", "#e91e63"),
        ("Я", "#f06292"),
        ("Ο", "#673ab7"),
        ("李", "#ba68c8"),
    ],
)
def test_etag_is_latin1(avatar_chars, avatar_color):
    """avatar_chars can be non-latin, etag must be valid HTTP header"""
    result = AvatarResult(Mock(avatar_chars=avatar_chars, avatar_color=avatar_color))
    assert len(result.etag) > 0
    assert isinstance(result.etag, str)
    assert result.etag.encode("latin-1")
