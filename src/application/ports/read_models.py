"""Application ports for CQRS read models backed by database views."""

from datetime import date
from typing import Protocol, runtime_checkable

from src.application.dto.read_model import (
    CompetencyHistoryEntryDTO,
    PathProgressionSummaryDTO,
)
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.path_id import PathId


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
