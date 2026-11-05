"""MeasurementId value object for type-safe competency measurement identification."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class MeasurementId:
    """
    Value object representing a unique competency measurement identifier.

    Immutable identifier using UUID for measurements inside an evaluation.
    Provides type safety and prevents mixing measurement IDs with other IDs.
    """

    value: UUID

    @classmethod
    def generate(cls) -> MeasurementId:
        """Generate a new unique MeasurementId."""
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_string: str) -> MeasurementId:
        """
        Create MeasurementId from string representation.

        Args:
            id_string: String representation of UUID

        Raises:
            ValueError: If string is not a valid UUID format
        """
        try:
            return cls(value=UUID(id_string))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid MeasurementId format: {id_string}") from e

    def __str__(self) -> str:
        """Return string representation of the ID."""
        return str(self.value)

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"MeasurementId({self.value})"
