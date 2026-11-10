"""DRF ViewSet for competency catalog operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.group_id import GroupId
from src.presentation.api.serializers.competency_serializers import (
    CompetencyCreateSerializer,
    CompetencyResponseSerializer,
)
from src.presentation.dependencies.container import Container, get_container


class CompetencyViewSet(viewsets.ViewSet):
    """
    ViewSet orchestrating competency catalog CRUD actions through application use cases.
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
        List all competencies, optionally filtered by category or group.

        Query parameters:
        - `category_id`: UUID filter for category.
        - `group_id`: UUID filter for competency group.
        """
        category_param = request.query_params.get("category_id")
        group_param = request.query_params.get("group_id")

        category_id = CategoryId(UUID(category_param)) if category_param else None
        group_id = GroupId(UUID(group_param)) if group_param else None

        competencies = self.container.list_competencies_use_case.execute(
            category_id=category_id,
            group_id=group_id,
        )
        serialized = [CompetencyResponseSerializer.from_dto(c) for c in competencies]
        return Response(serialized, status=status.HTTP_200_OK)

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        """Retrieve a single competency by UUID."""
        competency_id = CompetencyId(UUID(str(pk)))
        competency = self.container.get_competency_use_case.execute(competency_id)
        return Response(
            CompetencyResponseSerializer.from_dto(competency),
            status=status.HTTP_200_OK,
        )

    def create(self, request: Request) -> Response:
        """Create a new competency in the catalog."""
        serializer = CompetencyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.to_dto()
        created = self.container.create_competency_use_case.execute(dto)
        return Response(
            CompetencyResponseSerializer.from_dto(created),
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request: Request, pk: str | None = None) -> Response:
        """Delete an unreferenced competency from the catalog."""
        competency_id = CompetencyId(UUID(str(pk)))
        self.container.delete_competency_use_case.execute(competency_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
