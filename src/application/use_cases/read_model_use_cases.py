"""Use cases for querying CQRS read models."""

from __future__ import annotations

from datetime import date

from src.application.dto.read_model_dtos import (
    CompetencyHistoryEntryDTO,
    PathProgressionSummaryDTO,
)
from src.application.ports.read_models import (
    CompetencyHistoryReadModel,
    PathProgressionReadModel,
)
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.path_id import PathId


class GetCompetencyHistoryUseCase:
    """Use case for querying temporal competency history for a collaborator."""

    def __init__(self, read_model: CompetencyHistoryReadModel) -> None:
        """
        Initialize the use case with its read model port.

        Args:
            read_model: Read model port querying the history database view.
        """
        self._read_model = read_model

    def execute(
        self,
        collaborator_id: CollaboratorId,
        *,
        competency_id: CompetencyId | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[CompetencyHistoryEntryDTO]:
        """
        Query chronological competency history for a collaborator.

        Args:
            collaborator_id: Collaborator whose history is queried.
            competency_id: Optional competency filter.
            start_date: Optional start date filter.
            end_date: Optional end date filter.

        Returns:
            List of competency history entry DTOs.
        """
        return self._read_model.get_history(
            collaborator_id,
            competency_id=competency_id,
            start_date=start_date,
            end_date=end_date,
        )


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
