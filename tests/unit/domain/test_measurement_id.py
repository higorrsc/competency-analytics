"""Unit tests for MeasurementId value object."""

from uuid import UUID

import pytest

from src.domain.value_objects.measurement_id import MeasurementId


class TestMeasurementId:
    """Test MeasurementId value object."""

    def test_generate_creates_unique_ids(self) -> None:
        """Verify generate creates unique MeasurementId instances."""
        assert MeasurementId.generate() != MeasurementId.generate()

    def test_from_string_valid_uuid(self) -> None:
        """Verify from_string creates MeasurementId from a valid UUID string."""
        uuid_string = "623e4567-e89b-12d3-a456-426614174000"
        measurement_id = MeasurementId.from_string(uuid_string)

        assert str(measurement_id.value) == uuid_string

    def test_from_string_invalid_format_raises_error(self) -> None:
        """Verify from_string raises ValueError for an invalid UUID."""
        with pytest.raises(ValueError, match="Invalid MeasurementId format"):
            MeasurementId.from_string("not-a-uuid")

    def test_equality(self) -> None:
        """Verify equal UUIDs produce equal MeasurementIds."""
        uuid_value = UUID("623e4567-e89b-12d3-a456-426614174000")

        assert MeasurementId(uuid_value) == MeasurementId(uuid_value)

    def test_immutability(self) -> None:
        """Verify MeasurementId is immutable."""
        measurement_id = MeasurementId.generate()

        with pytest.raises(AttributeError):
            measurement_id.value = UUID("623e4567-e89b-12d3-a456-426614174000")  # type: ignore[misc]
