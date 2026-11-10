"""Django read model querying the path_progression_summary database view."""

from __future__ import annotations

from src.application.dto.read_model import PathProgressionSummaryDTO
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_id import PathId
from src.infrastructure.django.models.path_progression_summary_view import (
    PathProgressionSummaryViewModel,
)


class DjangoPathProgressionReadModel:
    """
    Read model adapter querying the path_progression_summary database view.

    Calculates path level requirement completion percentage against the
    collaborator's latest finalized evaluation.
    """

    def get_progression_summary(
        self,
        collaborator_id: CollaboratorId,
        path_id: PathId,
    ) -> PathProgressionSummaryDTO | None:
        """
        Return progression toward collaborator's active target level.

        Args:
            collaborator_id: Collaborator whose progression is queried.
            path_id: Career path of the active enrollment.

        Returns:
            The progression summary DTO, or None if no active enrollment or
            no finalized evaluation exists.
        """
        row = PathProgressionSummaryViewModel.objects.filter(
            collaborator_id=collaborator_id.value,
            path_id=path_id.value,
        ).first()

        if row is None:
            return None

        return PathProgressionSummaryDTO(
            collaborator_id=row.collaborator_id,
            path_id=row.path_id,
            target_level=str(row.target_level),
            total_requirements=row.total_requirements,
            requirements_met=row.requirements_met,
            completion_percentage=float(row.completion_percentage),
        )
