"""Unit tests for competency domain exceptions."""

from src.domain.exceptions.competency_errors import (
    CompetencyReferencedError,
    CompetencyValidationError,
)
from src.domain.exceptions.domain_error import DomainError
from src.domain.value_objects.competency_id import CompetencyId


class TestCompetencyValidationError:
    """Test the competency validation error hierarchy."""

    def test_should_be_a_domain_error(self) -> None:
        """Validation errors are domain errors."""
        error = CompetencyValidationError("invalid competency")

        assert isinstance(error, DomainError)
        assert str(error) == "invalid competency"


class TestCompetencyReferencedError:
    """Test the competency deletion-prevention error."""

    def test_should_be_a_domain_error(self) -> None:
        """Referenced errors are domain errors."""
        competency_id = CompetencyId.generate()

        error = CompetencyReferencedError(competency_id)

        assert isinstance(error, DomainError)

    def test_should_expose_competency_id(self) -> None:
        """The error keeps the identifier for callers to inspect."""
        competency_id = CompetencyId.generate()

        error = CompetencyReferencedError(competency_id)

        assert error.competency_id == competency_id

    def test_should_build_message_without_references(self) -> None:
        """Without references the message still explains the failure."""
        competency_id = CompetencyId.generate()

        error = CompetencyReferencedError(competency_id)

        assert "is referenced and cannot be deleted" in str(error)
        assert str(competency_id) in str(error)
        assert error.referenced_by == []

    def test_should_build_message_listing_references(self) -> None:
        """The message lists the references blocking deletion."""
        competency_id = CompetencyId.generate()
        references = ["path Senior Engineer", "evaluation Q1 2026"]

        error = CompetencyReferencedError(competency_id, referenced_by=references)

        message = str(error)
        assert "path Senior Engineer" in message
        assert "evaluation Q1 2026" in message
        assert error.referenced_by == references

    def test_should_copy_reference_list(self) -> None:
        """The error owns its reference list."""
        references = ["path Senior Engineer"]

        error = CompetencyReferencedError(CompetencyId.generate(), references)
        references.append("evaluation Q1 2026")

        assert error.referenced_by == ["path Senior Engineer"]
