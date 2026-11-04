"""Domain exceptions for the evaluation aggregate."""

from src.domain.exceptions.domain_error import DomainError
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.domain.value_objects.measurement_id import MeasurementId


class EvaluationValidationError(DomainError):
    """
    Raised when an evaluation or measurement violates an invariant.

    Examples include blank periods, duplicate competency measurements, and
    submissions without measurements.
    """


class EvaluationImmutableError(DomainError):
    """
    Raised when a modification is attempted on a non-draft evaluation.

    Measurements can only be changed while the evaluation is a draft, and
    finalized evaluations (accepted or contested) cannot be changed at all.
    """


class InvalidStatusTransitionError(DomainError):
    """
    Raised when a lifecycle transition is not allowed from the current status.

    Attributes:
        current: Status the evaluation is currently in.
        target: Status the caller attempted to reach.
    """

    def __init__(
        self,
        current: EvaluationStatus,
        target: EvaluationStatus,
    ) -> None:
        """
        Create an InvalidStatusTransitionError.

        Args:
            current: Status the evaluation is currently in.
            target: Status the caller attempted to reach.
        """
        self.current = current
        self.target = target
        super().__init__(f"Cannot transition evaluation from {current.value} to {target.value}")


class MeasurementNotFoundError(DomainError):
    """
    Raised when a measurement cannot be found inside an evaluation.

    Attributes:
        measurement_id: Identifier of the measurement that could not be found.
    """

    def __init__(self, measurement_id: MeasurementId) -> None:
        """
        Create a MeasurementNotFoundError.

        Args:
            measurement_id: Identifier of the missing measurement.
        """
        self.measurement_id = measurement_id
        super().__init__(f"Evaluation measurement {measurement_id} was not found")
