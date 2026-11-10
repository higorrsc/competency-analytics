"""Query use case for collaborator path progression summary."""

from __future__ import annotations

from src.application.dto.read_model import PathProgressionSummaryDTO
from src.application.ports.read_models import PathProgressionReadModel
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_id import PathId


class GetPathProgressionUseCase:
    """Use case for querying career path progression for a collaborator."""

    def __init__(self, read_model: PathProgressionReadModel) -> None:
        """
        Initialize the use case with its read model port.

        Args:
            read_model: Read model port querying the progression summary view.
        """
        self._read_model = read_model

    def execute(
        self,
        collaborator_id: CollaboratorId,
        path_id: PathId,
    ) -> PathProgressionSummaryDTO | None:
        """
        Query progression summary toward the active path target level.

        Args:
            collaborator_id: Collaborator whose progression is queried.
            path_id: Active career path identifier.

        Returns:
            Progression summary DTO or None if no progression is found.
        """
        return self._read_model.get_progression_summary(collaborator_id, path_id)
