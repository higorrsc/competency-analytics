"""DRF ViewSet for collaborator management and career path enrollments."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_id import PathId
from src.presentation.api.serializers.collaborator_serializers import (
    ActivatePathSerializer,
    CollaboratorCreateSerializer,
    CollaboratorResponseSerializer,
    EnrollmentCreateSerializer,
)
from src.presentation.dependencies.container import Container, get_container


class CollaboratorViewSet(viewsets.ViewSet):
    """
    ViewSet orchestrating collaborator registration and career path enrollments.
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
        """List collaborators, optionally filtered by career path."""
        path_param = request.query_params.get("path_id")
        active_only = request.query_params.get("active_only", "false").lower() == "true"
        path_id = PathId(UUID(path_param)) if path_param else None

        collaborators = self.container.list_collaborators_use_case.execute(
            path_id=path_id,
            active_only=active_only,
        )
        serialized = [CollaboratorResponseSerializer.from_dto(c) for c in collaborators]
        return Response(serialized, status=status.HTTP_200_OK)

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        """Retrieve a collaborator by UUID with their enrollment history."""
        collaborator_id = CollaboratorId(UUID(str(pk)))
        collaborator = self.container.get_collaborator_use_case.execute(collaborator_id)
        return Response(
            CollaboratorResponseSerializer.from_dto(collaborator),
            status=status.HTTP_200_OK,
        )

    def create(self, request: Request) -> Response:
        """Register a new collaborator."""
        serializer = CollaboratorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.to_dto()
        created = self.container.create_collaborator_use_case.execute(dto)
        return Response(
            CollaboratorResponseSerializer.from_dto(created),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="enroll")
    def enroll(self, request: Request, pk: str | None = None) -> Response:
        """Enroll the collaborator in a career path with a target level."""
        collaborator_id = CollaboratorId(UUID(str(pk)))
        serializer = EnrollmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.to_dto()
        updated = self.container.enroll_collaborator_in_path_use_case.execute(
            collaborator_id, dto
        )
        return Response(
            CollaboratorResponseSerializer.from_dto(updated),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="activate-path")
    def activate_path(self, request: Request, pk: str | None = None) -> Response:
        """Activate an existing enrollment, deactivating any previous active path."""
        collaborator_id = CollaboratorId(UUID(str(pk)))
        serializer = ActivatePathSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        path_id = PathId(serializer.validated_data["path_id"])
        updated = self.container.activate_collaborator_path_use_case.execute(
            collaborator_id, path_id
        )
        return Response(
            CollaboratorResponseSerializer.from_dto(updated),
            status=status.HTTP_200_OK,
        )
