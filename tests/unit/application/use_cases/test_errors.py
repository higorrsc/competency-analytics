"""Unit tests for application error types and use case documentation."""

import inspect

import pytest

from src.application.use_cases.collaborator.command import (
    EnrollCollaboratorInPathUseCase,
)
from src.application.use_cases.competency.command import (
    CreateCompetencyUseCase,
)
from src.application.use_cases.errors import (
    ApplicationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.application.use_cases.evaluation.command import (
    AcceptEvaluationUseCase,
    AddMeasurementToEvaluationUseCase,
    ContestEvaluationUseCase,
    CreateEvaluationUseCase,
    SubmitEvaluationUseCase,
)
from src.application.use_cases.gap_analysis.query import (
    CalculateCompetencyGapsUseCase,
)
from src.application.use_cases.path.command import CreateCareerPathUseCase

ALL_USE_CASES = [
    AcceptEvaluationUseCase,
    AddMeasurementToEvaluationUseCase,
    CalculateCompetencyGapsUseCase,
    ContestEvaluationUseCase,
    CreateCareerPathUseCase,
    CreateCompetencyUseCase,
    CreateEvaluationUseCase,
    EnrollCollaboratorInPathUseCase,
    SubmitEvaluationUseCase,
]


class TestApplicationErrorHierarchy:
    """Test the application error vocabulary used across use cases."""

    def test_all_concrete_errors_extend_application_error(self) -> None:
        """Concrete errors share the ApplicationError base."""
        assert issubclass(ValidationError, ApplicationError)
        assert issubclass(ConflictError, ApplicationError)
        assert issubclass(NotFoundError, ApplicationError)

    def test_error_messages_are_preserved(self) -> None:
        """Errors carry the original failure message."""
        error = ConflictError("finalized evaluation is immutable")

        assert error.message == "finalized evaluation is immutable"
        assert str(error) == "finalized evaluation is immutable"

    def test_not_found_error_identifies_entity(self) -> None:
        """Not-found errors carry entity and identifier fields."""
        error = NotFoundError("Collaborator", "abc")

        assert error.entity == "Collaborator"
        assert error.identifier == "abc"
        assert str(error) == "Collaborator not found: abc"


class TestUseCaseDocumentation:
    """Test that every use case publicly documents its orchestration flow."""

    @pytest.mark.parametrize("use_case", ALL_USE_CASES)
    def test_use_case_documents_orchestration(self, use_case: type) -> None:
        """Use case classes and execute methods have informative docs."""
        assert use_case.__doc__ is not None
        assert len(inspect.getdoc(use_case) or "") >= 40
        assert "Raises" in (inspect.getdoc(use_case.execute) or "")
