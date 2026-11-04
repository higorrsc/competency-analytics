"""Unit tests for CollaboratorId value object."""

from uuid import UUID

import pytest

from src.domain.value_objects.collaborator_id import CollaboratorId


class TestCollaboratorId:
    """Test CollaboratorId value object creation and validation."""

    def test_generate_creates_unique_ids(self) -> None:
        """Verify generate creates unique CollaboratorId instances."""
        id1 = CollaboratorId.generate()
        id2 = CollaboratorId.generate()

        assert id1 != id2
        assert isinstance(id1.value, UUID)
        assert isinstance(id2.value, UUID)

    def test_from_string_valid_uuid(self) -> None:
        """Verify from_string creates CollaboratorId from valid UUID string."""
        uuid_string = "123e4567-e89b-12d3-a456-426614174000"
        collaborator_id = CollaboratorId.from_string(uuid_string)

        assert str(collaborator_id.value) == uuid_string
        assert isinstance(collaborator_id, CollaboratorId)

    def test_from_string_invalid_format_raises_error(self) -> None:
        """Verify from_string raises ValueError for invalid UUID format."""
        with pytest.raises(ValueError, match="Invalid CollaboratorId format"):
            CollaboratorId.from_string("not-a-uuid")

    def test_equality(self) -> None:
        """Verify two CollaboratorIds with same UUID are equal."""
        uuid_value = UUID("123e4567-e89b-12d3-a456-426614174000")
        id1 = CollaboratorId(uuid_value)
        id2 = CollaboratorId(uuid_value)

        assert id1 == id2
        assert hash(id1) == hash(id2)

    def test_inequality(self) -> None:
        """Verify two CollaboratorIds with different UUIDs are not equal."""
        id1 = CollaboratorId.generate()
        id2 = CollaboratorId.generate()

        assert id1 != id2

    def test_immutability(self) -> None:
        """Verify CollaboratorId is immutable (frozen dataclass)."""
        collaborator_id = CollaboratorId.generate()

        with pytest.raises(AttributeError):
            collaborator_id.value = UUID("123e4567-e89b-12d3-a456-426614174000")  # type: ignore

    def test_string_representation(self) -> None:
        """Verify __str__ returns string representation of UUID."""
        uuid_string = "123e4567-e89b-12d3-a456-426614174000"
        collaborator_id = CollaboratorId.from_string(uuid_string)

        assert str(collaborator_id) == uuid_string

    def test_repr_representation(self) -> None:
        """Verify __repr__ returns developer-friendly representation."""
        uuid_value = UUID("123e4567-e89b-12d3-a456-426614174000")
        collaborator_id = CollaboratorId(uuid_value)

        assert repr(collaborator_id) == f"CollaboratorId({uuid_value})"
