"""Unit tests for evaluation domain exceptions."""

from src.domain.exceptions.domain_error import DomainError
from src.domain.exceptions.evaluation_errors import (
    EvaluationImmutableError,
    EvaluationValidationError,
    InvalidStatusTransitionError,
    MeasurementNotFoundError,
)
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.domain.value_objects.measurement_id import MeasurementId


class TestEvaluationValidationError:
    """Test the evaluation validation error."""

    def test_should_be_a_domain_error(self) -> None:
        """Validation errors are domain errors."""
        error = EvaluationValidationError("invalid evaluation")

        assert isinstance(error, DomainError)
        assert str(error) == "invalid evaluation"


class TestEvaluationImmutableError:
    """Test the immutability error."""

    def test_should_be_a_domain_error(self) -> None:
        """Immutability errors are domain errors."""
        error = EvaluationImmutableError("evaluation is immutable")

        assert isinstance(error, DomainError)
        assert str(error) == "evaluation is immutable"


class TestInvalidStatusTransitionError:
    """Test the invalid transition error."""

    def test_should_expose_current_and_target_statuses(self) -> None:
        """The error keeps both statuses for callers to inspect."""
        error = InvalidStatusTransitionError(
            EvaluationStatus.DRAFT,
            EvaluationStatus.ACCEPTED,
        )

        assert error.current is EvaluationStatus.DRAFT
        assert error.target is EvaluationStatus.ACCEPTED

    def test_should_build_descriptive_message(self) -> None:
        """The message names both statuses."""
        error = InvalidStatusTransitionError(
            EvaluationStatus.COMPLETED,
            EvaluationStatus.CONTESTED,
        )

        assert "COMPLETED" in str(error)
        assert "CONTESTED" in str(error)

    def test_should_be_a_domain_error(self) -> None:
        """Invalid transitions are domain errors."""
        error = InvalidStatusTransitionError(
            EvaluationStatus.DRAFT,
            EvaluationStatus.COMPLETED,
        )

        assert isinstance(error, DomainError)


class TestMeasurementNotFoundError:
    """Test the missing-measurement error."""

    def test_should_expose_measurement_id(self) -> None:
        """The error keeps the identifier for callers to inspect."""
        measurement_id = MeasurementId.generate()

        error = MeasurementNotFoundError(measurement_id)

        assert error.measurement_id == measurement_id

    def test_should_build_descriptive_message(self) -> None:
        """The message names the missing measurement."""
        measurement_id = MeasurementId.generate()

        error = MeasurementNotFoundError(measurement_id)

        assert str(measurement_id) in str(error)
        assert "was not found" in str(error)

    def test_should_be_a_domain_error(self) -> None:
        """Missing measurements are domain errors."""
        error = MeasurementNotFoundError(MeasurementId.generate())

        assert isinstance(error, DomainError)
