"""Application port for the collaborator competency history read model."""

from datetime import date
from typing import Protocol, runtime_checkable

from src.application.dto.read_model import CompetencyHistoryEntryDTO
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId


@runtime_checkable
class CompetencyHistoryReadModel(Protocol):
    """
    Read model for temporal competency queries.

    Implementations query optimized database views instead of loading whole
    aggregates, which keeps multi-year history queries efficient. Contracts
    return application DTOs, never domain aggregates.
    """

    def get_history(
        self,
        collaborator_id: CollaboratorId,
        *,
        competency_id: CompetencyId | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[CompetencyHistoryEntryDTO]:
        """
        Query competency evolution over time for a collaborator.

        Args:
            collaborator_id: Collaborator whose history is queried.
            competency_id: When provided, restrict the history to one
                competency.
            start_date: When provided, exclude evaluations before this date.
            end_date: When provided, exclude evaluations after this date.

        Returns:
            History entries ordered chronologically, including the previous
            level and change for each measurement when available.
        """
        ...
