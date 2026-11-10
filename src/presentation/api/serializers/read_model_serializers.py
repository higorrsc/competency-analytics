"""Serializers for CQRS read models backed by database views."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from src.application.dto.read_model import (
    CompetencyHistoryEntryDTO,
    PathProgressionSummaryDTO,
)


class CompetencyHistoryItemSerializer(serializers.Serializer[dict[str, Any]]):
    """Output serializer for temporal competency history entries."""

    collaborator_id = serializers.UUIDField()
    competency_id = serializers.UUIDField()
    competency_name = serializers.CharField()
    evaluation_date = serializers.DateTimeField()
    period = serializers.CharField()
    current_level = serializers.IntegerField()
    previous_level = serializers.IntegerField(allow_null=True)
    level_change = serializers.IntegerField(allow_null=True)
    status = serializers.CharField()

    @classmethod
    def from_dto(cls, dto: CompetencyHistoryEntryDTO) -> dict[str, Any]:
        """Serialize a CompetencyHistoryEntryDTO."""
        return {
            "collaborator_id": dto.collaborator_id,
            "competency_id": dto.competency_id,
            "competency_name": dto.competency_name,
            "evaluation_date": dto.evaluation_date,
            "period": dto.period,
            "current_level": dto.current_level,
            "previous_level": dto.previous_level,
            "level_change": dto.level_change,
            "status": dto.status.value,
        }


class PathProgressionSummarySerializer(serializers.Serializer[dict[str, Any]]):
    """Output serializer for career path progression summary."""

    collaborator_id = serializers.UUIDField()
    path_id = serializers.UUIDField()
    target_level = serializers.CharField()
    total_requirements = serializers.IntegerField()
    requirements_met = serializers.IntegerField()
    completion_percentage = serializers.FloatField()

    @classmethod
    def from_dto(cls, dto: PathProgressionSummaryDTO) -> dict[str, Any]:
        """Serialize a PathProgressionSummaryDTO."""
        return {
            "collaborator_id": dto.collaborator_id,
            "path_id": dto.path_id,
            "target_level": dto.target_level,
            "total_requirements": dto.total_requirements,
            "requirements_met": dto.requirements_met,
            "completion_percentage": dto.completion_percentage,
        }
