"""Domain exceptions for the competency catalog aggregate."""

from src.domain.exceptions.domain_error import DomainError
from src.domain.value_objects.competency_id import CompetencyId


class CompetencyValidationError(DomainError):
    """
    Raised when a competency violates catalog invariants.

    Examples include an empty name, missing proficiency level descriptions,
    invalid level numbers, or blank level descriptions.
    """


class CompetencyReferencedError(DomainError):
    """
    Raised when a competency cannot be deleted because it is referenced.

    A competency may not be removed while career paths require it or while
    evaluations contain measurements for it, because doing so would break
    historical and structural integrity.

    Attributes:
        competency_id: Identifier of the competency that could not be removed.
        referenced_by: Human-readable descriptions of the references that
            block the deletion (for example path or evaluation identifiers).
    """

    def __init__(
        self,
        competency_id: CompetencyId,
        referenced_by: list[str] | None = None,
    ) -> None:
        """
        Create a CompetencyReferencedError.

        Args:
            competency_id: Identifier of the referenced competency.
            referenced_by: Optional descriptions of the blocking references.
        """
        self.competency_id = competency_id
        self.referenced_by = list(referenced_by) if referenced_by else []
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        """Build a descriptive error message listing the blocking references."""
        base = f"Competency {self.competency_id} is referenced and cannot be deleted"
        if not self.referenced_by:
            return base
        references = ", ".join(self.referenced_by)
        return f"{base}: {references}"
