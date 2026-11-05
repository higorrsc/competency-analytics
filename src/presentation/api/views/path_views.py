"""DRF ViewSet for career path definition and level requirements."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from src.domain.value_objects.path_id import PathId
from src.presentation.api.serializers.path_serializers import (
    CareerPathCreateSerializer,
    CareerPathResponseSerializer,
)
from src.presentation.dependencies.container import Container, get_container


class CareerPathViewSet(viewsets.ViewSet):
    """
    ViewSet orchestrating career path operations through application use cases.
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
        """List all career paths with nested levels and competency requirements."""
        paths = self.container.list_career_paths_use_case.execute()
        serialized = [CareerPathResponseSerializer.from_dto(p) for p in paths]
        return Response(serialized, status=status.HTTP_200_OK)

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        """Retrieve a career path by UUID with its complete level hierarchy."""
        path_id = PathId(UUID(str(pk)))
        path = self.container.get_career_path_use_case.execute(path_id)
        return Response(
            CareerPathResponseSerializer.from_dto(path),
            status=status.HTTP_200_OK,
        )

    def create(self, request: Request) -> Response:
        """Create a new career path with ordered levels and competency requirements."""
        serializer = CareerPathCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.to_dto()
        created = self.container.create_career_path_use_case.execute(dto)
        return Response(
            CareerPathResponseSerializer.from_dto(created),
            status=status.HTTP_201_CREATED,
        )
