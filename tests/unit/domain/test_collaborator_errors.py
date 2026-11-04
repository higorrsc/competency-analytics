"""Unit tests for collaborator domain exceptions."""

from src.domain.exceptions.collaborator_errors import (
    CollaboratorValidationError,
    EnrollmentNotFoundError,
)
from src.domain.exceptions.domain_error import DomainError
from src.domain.value_objects.path_id import PathId


class TestCollaboratorValidationError:
    """Test the collaborator validation error."""

    def test_should_be_a_domain_error(self) -> None:
        """Validation errors are domain errors."""
        error = CollaboratorValidationError("invalid collaborator")

        assert isinstance(error, DomainError)
        assert str(error) == "invalid collaborator"


class TestEnrollmentNotFoundError:
    """Test the missing-enrollment error."""

    def test_should_be_a_domain_error(self) -> None:
        """Missing-enrollment errors are domain errors."""
        error = EnrollmentNotFoundError(PathId.generate())

        assert isinstance(error, DomainError)

    def test_should_expose_path_id(self) -> None:
        """The error keeps the path identifier for callers to inspect."""
        path_id = PathId.generate()

        error = EnrollmentNotFoundError(path_id)

        assert error.path_id == path_id

    def test_should_build_descriptive_message(self) -> None:
        """The message names the path without an enrollment."""
        path_id = PathId.generate()

        error = EnrollmentNotFoundError(path_id)

        assert str(path_id) in str(error)
        assert "not enrolled" in str(error)
