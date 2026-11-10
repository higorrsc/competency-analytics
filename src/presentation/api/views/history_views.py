"""DRF view for querying temporal competency history via CQRS read model."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.presentation.api.serializers.read_model_serializers import (
    CompetencyHistoryItemSerializer,
)
from src.presentation.dependencies.container import Container, get_container


class CompetencyHistoryViewSet(viewsets.ViewSet):
    """
    Read-only ViewSet querying chronological competency evolution for collaborators.
    """

    def __init__(
        self,
        *args: Any,
        container: Container | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.container = container or get_container()

    def list(self, request: Request) -> Response:
        """
        Query chronological competency history for a collaborator.

        Query parameters:
        - `collaborator_id` (mandatory): Collaborator UUID.
        - `competency_id` (optional): Competency UUID.
        - `start_date` (optional): ISO format date filter (YYYY-MM-DD).
        - `end_date` (optional): ISO format date filter (YYYY-MM-DD).
        """
        collab_param = request.query_params.get("collaborator_id")
        if not collab_param:
            raise DRFValidationError(
                {"collaborator_id": "This query parameter is required."}
            )

        collaborator_id = CollaboratorId(UUID(collab_param))
        comp_param = request.query_params.get("competency_id")
        competency_id = CompetencyId(UUID(comp_param)) if comp_param else None

        start_date: date | None = None
        end_date: date | None = None
        start_param = request.query_params.get("start_date")
        if start_param:
            start_date = date.fromisoformat(start_param)
        end_param = request.query_params.get("end_date")
        if end_param:
            end_date = date.fromisoformat(end_param)

        entries = self.container.get_competency_history_use_case.execute(
            collaborator_id,
            competency_id=competency_id,
            start_date=start_date,
            end_date=end_date,
        )
        serialized = [CompetencyHistoryItemSerializer.from_dto(e) for e in entries]
        return Response(serialized, status=status.HTTP_200_OK)
