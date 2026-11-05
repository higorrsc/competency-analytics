"""DRF ViewSet for competency evaluation lifecycle and measurement management."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.evaluation_id import EvaluationId
from src.presentation.api.serializers.evaluation_serializers import (
    EvaluationAcceptSerializer,
    EvaluationContestSerializer,
    EvaluationCreateSerializer,
    EvaluationResponseSerializer,
    MeasurementCreateSerializer,
)
from src.presentation.dependencies.container import Container, get_container


class EvaluationViewSet(viewsets.ViewSet):
    """
    ViewSet orchestrating evaluation lifecycle transitions and measurements.
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
        """List evaluations, optionally filtered by collaborator UUID."""
        collab_param = request.query_params.get("collaborator_id")
        collaborator_id = CollaboratorId(UUID(collab_param)) if collab_param else None
        evaluations = self.container.list_evaluations_use_case.execute(
            collaborator_id=collaborator_id
        )
        serialized = [EvaluationResponseSerializer.from_dto(e) for e in evaluations]
        return Response(serialized, status=status.HTTP_200_OK)

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        """Retrieve an evaluation by UUID with its current measurements and state."""
        evaluation_id = EvaluationId(UUID(str(pk)))
        evaluation = self.container.get_evaluation_use_case.execute(evaluation_id)
        return Response(
            EvaluationResponseSerializer.from_dto(evaluation),
            status=status.HTTP_200_OK,
        )

    def create(self, request: Request) -> Response:
        """Initialize a new evaluation in draft (RASCUNHO) state."""
        serializer = EvaluationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.to_dto()
        created = self.container.create_evaluation_use_case.execute(dto)
        return Response(
            EvaluationResponseSerializer.from_dto(created),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="measurements")
    def add_measurement(self, request: Request, pk: str | None = None) -> Response:
        """Add a competency measurement to an evaluation in draft state."""
        evaluation_id = EvaluationId(UUID(str(pk)))
        serializer = MeasurementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.to_dto()
        updated = self.container.add_measurement_to_evaluation_use_case.execute(
            evaluation_id, dto
        )
        return Response(
            EvaluationResponseSerializer.from_dto(updated),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request: Request, pk: str | None = None) -> Response:
        """Transition evaluation from draft to completed (CONCLUÍDA)."""
        evaluation_id = EvaluationId(UUID(str(pk)))
        updated = self.container.submit_evaluation_use_case.execute(evaluation_id)
        return Response(
            EvaluationResponseSerializer.from_dto(updated),
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="accept")
    def accept(self, request: Request, pk: str | None = None) -> Response:
        """Collaborator accepts the evaluation, finalizing it as ACEITA."""
        evaluation_id = EvaluationId(UUID(str(pk)))
        serializer = EvaluationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notes = serializer.validated_data.get("response_notes") or None
        updated = self.container.accept_evaluation_use_case.execute(
            evaluation_id, response_notes=notes
        )
        return Response(
            EvaluationResponseSerializer.from_dto(updated),
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="contest")
    def contest(self, request: Request, pk: str | None = None) -> Response:
        """
        Collaborator contests evaluation, finalizing as CONTESTADA (notes required).
        """
        evaluation_id = EvaluationId(UUID(str(pk)))
        serializer = EvaluationContestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notes = serializer.validated_data["response_notes"]
        updated = self.container.contest_evaluation_use_case.execute(
            evaluation_id, response_notes=notes
        )
        return Response(
            EvaluationResponseSerializer.from_dto(updated),
            status=status.HTTP_200_OK,
        )
