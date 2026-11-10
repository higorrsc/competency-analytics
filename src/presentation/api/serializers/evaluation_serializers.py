"""Serializers for evaluation lifecycle and competency measurements."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from rest_framework import serializers

from src.application.dto.evaluation import (
    EvaluationCreateDTO,
    EvaluationResponseDTO,
    MeasurementCreateDTO,
    MeasurementDTO,
)


class MeasurementCreateSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for adding a competency measurement to a draft evaluation."""

    competency_id = serializers.UUIDField()
    current_level = serializers.IntegerField(min_value=1, max_value=5)
    notes = serializers.CharField(allow_blank=True, default="", required=False)
    evidence = serializers.CharField(allow_blank=True, default="", required=False)

    def to_dto(self) -> MeasurementCreateDTO:
        """Convert validated serializer data to MeasurementCreateDTO."""
        data = self.validated_data
        return MeasurementCreateDTO(
            competency_id=data["competency_id"],
            current_level=data["current_level"],
            notes=data.get("notes") or None,
            evidence=data.get("evidence") or None,
        )


class EvaluationCreateSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for initializing an evaluation in draft state."""

    collaborator_id = serializers.UUIDField()
    evaluator_id = serializers.UUIDField()
    period = serializers.CharField(max_length=50)
    evaluation_date = serializers.DateTimeField(required=False)

    def to_dto(self) -> EvaluationCreateDTO:
        """Convert validated serializer data to EvaluationCreateDTO."""
        data = self.validated_data
        return EvaluationCreateDTO(
            collaborator_id=data["collaborator_id"],
            evaluator_id=data["evaluator_id"],
            period=data["period"],
            evaluation_date=data.get("evaluation_date") or datetime.now(UTC),
        )


class EvaluationAcceptSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for accepting a completed evaluation."""

    response_notes = serializers.CharField(allow_blank=True, default="", required=False)


class EvaluationContestSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for contesting an evaluation (notes required)."""

    response_notes = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={"blank": "Contestation notes are mandatory"},
    )


class MeasurementResponseSerializer(serializers.Serializer[dict[str, Any]]):
    """Output serializer for a single competency measurement."""

    id = serializers.UUIDField()
    competency_id = serializers.UUIDField()
    current_level = serializers.IntegerField()
    notes = serializers.CharField(allow_null=True)
    evidence = serializers.CharField(allow_null=True)

    @classmethod
    def from_dto(cls, dto: MeasurementDTO) -> dict[str, Any]:
        """Serialize a MeasurementDTO."""
        return {
            "id": dto.id,
            "competency_id": dto.competency_id,
            "current_level": dto.current_level,
            "notes": dto.notes,
            "evidence": dto.evidence,
        }


class EvaluationResponseSerializer(serializers.Serializer[dict[str, Any]]):
    """Output serializer for complete evaluation state and measurements."""

    id = serializers.UUIDField()
    collaborator_id = serializers.UUIDField()
    evaluator_id = serializers.UUIDField()
    period = serializers.CharField()
    evaluation_date = serializers.DateTimeField()
    status = serializers.CharField()
    measurements = MeasurementResponseSerializer(many=True)
    submitted_at = serializers.DateTimeField(allow_null=True)
    response_date = serializers.DateTimeField(allow_null=True)
    response_notes = serializers.CharField(allow_null=True)

    @classmethod
    def from_dto(cls, dto: EvaluationResponseDTO) -> dict[str, Any]:
        """Serialize an EvaluationResponseDTO."""
        return {
            "id": dto.id,
            "collaborator_id": dto.collaborator_id,
            "evaluator_id": dto.evaluator_id,
            "period": dto.period,
            "evaluation_date": dto.evaluation_date,
            "status": dto.status.value,
            "measurements": [
                MeasurementResponseSerializer.from_dto(m) for m in dto.measurements
            ],
            "submitted_at": dto.submitted_at,
            "response_date": dto.response_date,
            "response_notes": dto.response_notes,
        }
