"""Serializers for competency gap analysis and progression eligibility."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from rest_framework import serializers

from src.application.dto.gap_analysis import (
    CompetencyGapDTO,
    GapAnalysisRequestDTO,
    GapAnalysisResponseDTO,
    ProgressionEligibilityDTO,
)


class GapAnalysisRequestSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for calculating competency gaps against a target path level."""

    collaborator_id = serializers.UUIDField()
    path_id = serializers.UUIDField()
    level_id = serializers.UUIDField()

    def to_dto(self) -> GapAnalysisRequestDTO:
        """Convert validated serializer data to GapAnalysisRequestDTO."""
        data = self.validated_data
        return GapAnalysisRequestDTO(
            collaborator_id=data["collaborator_id"],
            path_id=data["path_id"],
            level_id=data["level_id"],
        )


class CompetencyGapResponseSerializer(serializers.Serializer[dict[str, Any]]):
    """Output serializer for a single competency gap."""

    competency_id = serializers.UUIDField()
    current_level = serializers.IntegerField()
    required_level = serializers.IntegerField()
    gap = serializers.IntegerField()
    weight = serializers.CharField()

    @classmethod
    def from_dto(cls, dto: CompetencyGapDTO) -> dict[str, Any]:
        """Serialize a CompetencyGapDTO."""
        return {
            "competency_id": dto.competency_id,
            "current_level": dto.current_level,
            "required_level": dto.required_level,
            "gap": dto.gap,
            "weight": dto.weight.value,
        }


class ProgressionEligibilityResponseSerializer(serializers.Serializer[dict[str, Any]]):
    """Output serializer for progression eligibility status."""

    is_eligible = serializers.BooleanField()
    blocking_competency_ids = serializers.ListField(child=serializers.UUIDField())

    @classmethod
    def from_dto(cls, dto: ProgressionEligibilityDTO) -> dict[str, Any]:
        """Serialize a ProgressionEligibilityDTO."""
        return {
            "is_eligible": dto.is_eligible,
            "blocking_competency_ids": dto.blocking_competency_ids,
        }


class GapAnalysisResponseSerializer(serializers.Serializer[dict[str, Any]]):
    """Output serializer for complete gap analysis with prioritized recommendations."""

    collaborator_id = serializers.UUIDField(required=False, allow_null=True)
    path_id = serializers.UUIDField(required=False, allow_null=True)
    level_id = serializers.UUIDField(required=False, allow_null=True)
    gaps = CompetencyGapResponseSerializer(many=True)
    eligibility = ProgressionEligibilityResponseSerializer()

    @classmethod
    def from_dto(
        cls,
        dto: GapAnalysisResponseDTO,
        *,
        collaborator_id: UUID | None = None,
        path_id: UUID | None = None,
        level_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Serialize a GapAnalysisResponseDTO."""
        return {
            "collaborator_id": collaborator_id,
            "path_id": path_id,
            "level_id": level_id,
            "gaps": [CompetencyGapResponseSerializer.from_dto(g) for g in dto.gaps],
            "eligibility": ProgressionEligibilityResponseSerializer.from_dto(
                dto.eligibility
            ),
        }
