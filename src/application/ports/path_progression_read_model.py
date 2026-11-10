"""Application port for the career path progression read model."""

from typing import Protocol, runtime_checkable

from src.application.dto.read_model import PathProgressionSummaryDTO
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_id import PathId


@runtime_checkable
class PathProgressionReadModel(Protocol):
    """
    Read model for path progression summaries.

    Implementations aggregate the database view that counts how many of the
    target level requirements are met by the collaborator's latest finalized
    evaluation.
    """

    def get_progression_summary(
        self,
        collaborator_id: CollaboratorId,
        path_id: PathId,
    ) -> PathProgressionSummaryDTO | None:
        """
        Return progression toward the collaborator's active target level.

        Args:
            collaborator_id: Collaborator whose progression is queried.
            path_id: Career path of the active enrollment.

        Returns:
            The progression summary, or ``None`` when the collaborator has no
            active enrollment in the path or no finalized evaluation yet.
        """
        ...
