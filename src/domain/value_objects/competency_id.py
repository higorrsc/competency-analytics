"""CompetencyId value object for type-safe competency identification."""

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class CompetencyId:
    """
    Value object representing a unique competency identifier.

    Immutable identifier using UUID for competencies in the system.
    Provides type safety and prevents mixing competency IDs with other entity IDs.
    """

    value: UUID

    @classmethod
    def generate(cls) -> "CompetencyId":
        """Generate a new unique CompetencyId."""
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_string: str) -> "CompetencyId":
        """
        Create CompetencyId from string representation.

        Args:
            id_string: String representation of UUID

        Raises:
            ValueError: If string is not a valid UUID format
        """
        try:
            return cls(value=UUID(id_string))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid CompetencyId format: {id_string}") from e

    def __str__(self) -> str:
        """Return string representation of the ID."""
        return str(self.value)

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"CompetencyId({self.value})"
