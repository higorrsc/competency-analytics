"""Unit tests for LevelId value object."""

from uuid import UUID

import pytest

from src.domain.value_objects.level_id import LevelId


class TestLevelId:
    """Test LevelId value object."""

    def test_generate_creates_unique_ids(self) -> None:
        """Verify generate creates unique LevelId instances."""
        assert LevelId.generate() != LevelId.generate()

    def test_from_string_valid_uuid(self) -> None:
        """Verify from_string creates LevelId from a valid UUID string."""
        uuid_string = "623e4567-e89b-12d3-a456-426614174000"
        level_id = LevelId.from_string(uuid_string)

        assert str(level_id.value) == uuid_string

    def test_from_string_invalid_format_raises_error(self) -> None:
        """Verify from_string raises ValueError for an invalid UUID."""
        with pytest.raises(ValueError, match="Invalid LevelId format"):
            LevelId.from_string("not-a-uuid")

    def test_equality(self) -> None:
        """Verify equal UUIDs produce equal LevelIds."""
        uuid_value = UUID("623e4567-e89b-12d3-a456-426614174000")

        assert LevelId(uuid_value) == LevelId(uuid_value)

    def test_immutability(self) -> None:
        """Verify LevelId is immutable."""
        level_id = LevelId.generate()

        with pytest.raises(AttributeError):
            level_id.value = UUID("623e4567-e89b-12d3-a456-426614174000")  # type: ignore[misc]
