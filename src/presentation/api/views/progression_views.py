"""DRF view for querying career path progression summary via CQRS read model."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_id import PathId
from src.presentation.api.serializers.read_model_serializers import (
    PathProgressionSummarySerializer,
)
from src.presentation.dependencies.container import Container, get_container


class PathProgressionViewSet(viewsets.ViewSet):
    """
    Read-only ViewSet querying career path progression summary.
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
        Query progression summary toward the active path target level.

        Query parameters:
        - `collaborator_id` (mandatory): Collaborator UUID.
        - `path_id` (mandatory): Career path UUID.
        """
        collab_param = request.query_params.get("collaborator_id")
        path_param = request.query_params.get("path_id")

        if not collab_param:
            raise DRFValidationError(
                {"collaborator_id": "This query parameter is required."}
            )
        if not path_param:
            raise DRFValidationError({"path_id": "This query parameter is required."})

        collaborator_id = CollaboratorId(UUID(collab_param))
        path_id = PathId(UUID(path_param))

        summary = self.container.get_path_progression_use_case.execute(
            collaborator_id, path_id
        )
        if summary is None:
            return Response(None, status=status.HTTP_200_OK)

        return Response(
            PathProgressionSummarySerializer.from_dto(summary),
            status=status.HTTP_200_OK,
        )
