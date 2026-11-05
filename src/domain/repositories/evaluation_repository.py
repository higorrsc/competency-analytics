"""Repository abstraction for the evaluation aggregate."""

from typing import Protocol, runtime_checkable

from src.domain.entities.evaluation import Evaluation
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.evaluation_id import EvaluationId


@runtime_checkable
class EvaluationRepository(Protocol):
    """
    Persistence contract for competency evaluations.

    The domain defines this contract; infrastructure provides the concrete
    implementation. Implementations MUST persist the evaluation together with
    its measurements and MUST NOT allow updates to finalized evaluations at
    the persistence level either.
    """

    def save(self, evaluation: Evaluation) -> None:
        """
        Persist an evaluation, creating or updating it.

        Args:
            evaluation: Aggregate to persist.
        """
        ...

    def get_by_id(self, evaluation_id: EvaluationId) -> Evaluation | None:
        """
        Retrieve an evaluation by identifier.

        Args:
            evaluation_id: Identifier of the evaluation.

        Returns:
            The evaluation when found, otherwise ``None``.
        """
        ...

    def find_latest_finalized_for_collaborator(
        self, collaborator_id: CollaboratorId
    ) -> Evaluation | None:
        """
        Return the most recent finalized evaluation for a collaborator.

        Finalized evaluations are those in ``ACCEPTED`` or ``CONTESTED``
        status. They provide the baseline for gap analysis and progression.

        Args:
            collaborator_id: Collaborator whose history is queried.

        Returns:
            The most recent finalized evaluation, or ``None`` when the
            collaborator has no finalized evaluation.
        """
        ...

    def find_all(
        self, *, collaborator_id: CollaboratorId | None = None
    ) -> list[Evaluation]:
        """
        Return evaluations, optionally filtered by collaborator.

        Args:
            collaborator_id: Optional collaborator filter.

        Returns:
            List of matching evaluations.
        """
        ...
