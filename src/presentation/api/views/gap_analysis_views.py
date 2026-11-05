"""DRF view for competency gap analysis against career path levels."""

from __future__ import annotations

from typing import Any

from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from src.presentation.api.serializers.gap_analysis_serializers import (
    GapAnalysisRequestSerializer,
    GapAnalysisResponseSerializer,
)
from src.presentation.dependencies.container import Container, get_container


class GapAnalysisViewSet(viewsets.ViewSet):
    """
    Read-only ViewSet calculating competency gaps and progression eligibility.
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
        Calculate competency gaps from query parameters.

        Query parameters:
        - `collaborator_id`: Collaborator UUID.
        - `path_id`: Career path UUID.
        - `level_id`: Target path level UUID.
        """
        serializer = GapAnalysisRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        dto = serializer.to_dto()
        result = self.container.calculate_competency_gaps_use_case.execute(dto)
        return Response(
            GapAnalysisResponseSerializer.from_dto(
                result,
                collaborator_id=dto.collaborator_id,
                path_id=dto.path_id,
                level_id=dto.level_id,
            ),
            status=status.HTTP_200_OK,
        )

    def create(self, request: Request) -> Response:
        """
        Calculate competency gaps from request body.

        Request body:
        - `collaborator_id`: Collaborator UUID.
        - `path_id`: Career path UUID.
        - `level_id`: Target path level UUID.
        """
        serializer = GapAnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.to_dto()
        result = self.container.calculate_competency_gaps_use_case.execute(dto)
        return Response(
            GapAnalysisResponseSerializer.from_dto(
                result,
                collaborator_id=dto.collaborator_id,
                path_id=dto.path_id,
                level_id=dto.level_id,
            ),
            status=status.HTTP_200_OK,
        )
