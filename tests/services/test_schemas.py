# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Ubiquity Press
#
# Invenio-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
#
"""Test suite for the schemas."""

import pytest
from marshmallow import ValidationError

from invenio_users_resources.services.schemas import GroupSchema


def test_group_schema():
    """Test group schema."""
    valid_input = {"name": "group-name", "description": "This is a valid description."}
    schema = GroupSchema()
    group = schema.load(valid_input)
    assert valid_input == group


def test_group_schema_errors():
    """Test group schema errors."""
    schema = GroupSchema()
    # Mising required informatin
    with pytest.raises(ValidationError) as exc_info:
        schema.load(
            {
                "description": "desc",
            }
        )
    assert exc_info.value.args[0] == {
        "name": [
            "Missing data for required field.",
        ]
    }
    # Wrong name
    with pytest.raises(ValidationError) as exc_info:
        schema.load(
            {
                "name": "name@wrong",
            }
        )
    assert exc_info.value.args[0] == {
        "name": [
            "Role name must start with a letter and contain only letters, numbers, "
            "hyphens or underscores (max 80 chars).",
        ]
    }
    # Name too long
    with pytest.raises(ValidationError) as exc_info:
        schema.load(
            {
                "name": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            }
        )
    assert exc_info.value.args[0] == {
        "name": [
            "Length must be between 1 and 80.",
            "Role name must start with a letter and contain only letters, numbers, "
            "hyphens or underscores (max 80 chars).",
        ]
    }
