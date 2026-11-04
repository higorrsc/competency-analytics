"""Unit tests for CategoryId and GroupId value objects."""

from uuid import UUID

import pytest

from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.group_id import GroupId


class TestCategoryId:
    """Test CategoryId value object."""

    def test_generate_creates_unique_ids(self) -> None:
        """Verify generate creates unique CategoryId instances."""
        assert CategoryId.generate() != CategoryId.generate()

    def test_from_string_valid_uuid(self) -> None:
        """Verify from_string creates CategoryId from a valid UUID string."""
        uuid_string = "423e4567-e89b-12d3-a456-426614174000"
        category_id = CategoryId.from_string(uuid_string)

        assert str(category_id.value) == uuid_string

    def test_from_string_invalid_format_raises_error(self) -> None:
        """Verify from_string raises ValueError for an invalid UUID."""
        with pytest.raises(ValueError, match="Invalid CategoryId format"):
            CategoryId.from_string("not-a-uuid")

    def test_equality(self) -> None:
        """Verify equal UUIDs produce equal CategoryIds."""
        uuid_value = UUID("423e4567-e89b-12d3-a456-426614174000")

        assert CategoryId(uuid_value) == CategoryId(uuid_value)


class TestGroupId:
    """Test GroupId value object."""

    def test_generate_creates_unique_ids(self) -> None:
        """Verify generate creates unique GroupId instances."""
        assert GroupId.generate() != GroupId.generate()

    def test_from_string_valid_uuid(self) -> None:
        """Verify from_string creates GroupId from a valid UUID string."""
        uuid_string = "523e4567-e89b-12d3-a456-426614174000"
        group_id = GroupId.from_string(uuid_string)

        assert str(group_id.value) == uuid_string

    def test_from_string_invalid_format_raises_error(self) -> None:
        """Verify from_string raises ValueError for an invalid UUID."""
        with pytest.raises(ValueError, match="Invalid GroupId format"):
            GroupId.from_string("not-a-uuid")

    def test_equality(self) -> None:
        """Verify equal UUIDs produce equal GroupIds."""
        uuid_value = UUID("523e4567-e89b-12d3-a456-426614174000")

        assert GroupId(uuid_value) == GroupId(uuid_value)
