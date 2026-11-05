"""Django read model querying the collaborator_competency_history database view."""

from __future__ import annotations

from datetime import UTC, date, datetime, time

from src.application.dto.read_model_dtos import CompetencyHistoryEntryDTO
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.infrastructure.django.models.collaborator_competency_history_view import (
    CollaboratorCompetencyHistoryViewModel,
)


class DjangoCompetencyHistoryReadModel:
    """
    Read model adapter querying the collaborator_competency_history database view.

    Provides chronological competency level history with previous levels and
    level changes computed by database window functions.
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
            competency_id: Optional filter for a specific competency.
            start_date: Optional inclusive start date filter.
            end_date: Optional inclusive end date filter.

        Returns:
            List of CompetencyHistoryEntryDTO ordered chronologically.
        """
        queryset = CollaboratorCompetencyHistoryViewModel.objects.filter(
            collaborator_id=collaborator_id.value
        )
        if competency_id is not None:
            queryset = queryset.filter(competency_id=competency_id.value)
        if start_date is not None:
            start_dt = datetime.combine(start_date, time.min, tzinfo=UTC)
            queryset = queryset.filter(evaluation_date__gte=start_dt)
        if end_date is not None:
            end_dt = datetime.combine(end_date, time.max, tzinfo=UTC)
            queryset = queryset.filter(evaluation_date__lte=end_dt)

        queryset = queryset.order_by("evaluation_date", "id")

        return [
            CompetencyHistoryEntryDTO(
                collaborator_id=row.collaborator_id,
                competency_id=row.competency_id,
                competency_name=str(row.competency_name),
                evaluation_date=row.evaluation_date,
                period=str(row.period),
                current_level=row.current_level,
                previous_level=row.previous_level,
                level_change=row.level_change,
                status=EvaluationStatus(row.status),
            )
            for row in queryset
        ]
