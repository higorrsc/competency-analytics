"""Serializers for career path and level endpoints."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from src.application.dto.path_dtos import (
    LevelCreateDTO,
    LevelResponseDTO,
    PathCreateDTO,
    PathResponseDTO,
    RequirementCreateDTO,
    RequirementResponseDTO,
)
from src.domain.value_objects.requirement_weight import RequirementWeight


class RequirementCreateSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for a competency requirement within a path level."""

    competency_id = serializers.UUIDField()
    minimum_level = serializers.IntegerField(min_value=1, max_value=5)
    weight = serializers.ChoiceField(
        choices=[w.value for w in RequirementWeight],
        default=RequirementWeight.CORE.value,
    )

    def to_dto(self) -> RequirementCreateDTO:
        """Convert validated input to application DTO."""
        data = self.validated_data
        return RequirementCreateDTO(
            competency_id=data["competency_id"],
            minimum_level=data["minimum_level"],
            weight=RequirementWeight(data["weight"]),
        )


class LevelCreateSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for a career path level."""

    name = serializers.CharField(max_length=100)
    order = serializers.IntegerField(min_value=1)
    requirements = RequirementCreateSerializer(many=True, default=list)

    def to_dto(self) -> LevelCreateDTO:
        """Convert validated input to application DTO."""
        data = self.validated_data
        reqs = [
            RequirementCreateDTO(
                competency_id=r["competency_id"],
                minimum_level=r["minimum_level"],
                weight=RequirementWeight(r["weight"]),
            )
            for r in data.get("requirements", [])
        ]
        return LevelCreateDTO(
            name=data["name"],
            order=data["order"],
            requirements=reqs,
        )


class CareerPathCreateSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for creating a career path with ordered levels."""

    name = serializers.CharField(max_length=200)
    description = serializers.CharField(allow_blank=True, default="")
    levels = LevelCreateSerializer(many=True)

    def to_dto(self) -> PathCreateDTO:
        """Convert validated input to application DTO."""
        data = self.validated_data
        levels: list[LevelCreateDTO] = []
        for l_data in data["levels"]:
            reqs = [
                RequirementCreateDTO(
                    competency_id=r["competency_id"],
                    minimum_level=r["minimum_level"],
                    weight=RequirementWeight(r["weight"]),
                )
                for r in l_data.get("requirements", [])
            ]
            levels.append(
                LevelCreateDTO(
                    name=l_data["name"],
                    order=l_data["order"],
                    requirements=reqs,
                )
            )
        return PathCreateDTO(
            name=data["name"],
            description=data.get("description", ""),
            levels=levels,
        )


class RequirementResponseSerializer(serializers.Serializer[dict[str, Any]]):
    """Output serializer for a competency requirement."""

    competency_id = serializers.UUIDField()
    minimum_level = serializers.IntegerField()
    weight = serializers.CharField()

    @classmethod
    def from_dto(cls, dto: RequirementResponseDTO) -> dict[str, Any]:
        """Serialize a RequirementResponseDTO."""
        return {
            "competency_id": dto.competency_id,
            "minimum_level": dto.minimum_level,
            "weight": dto.weight.value,
        }


class LevelResponseSerializer(serializers.Serializer[dict[str, Any]]):
    """Output serializer for a career path level with its requirements."""

    id = serializers.UUIDField()
    name = serializers.CharField()
    order = serializers.IntegerField()
    requirements = RequirementResponseSerializer(many=True)

    @classmethod
    def from_dto(cls, dto: LevelResponseDTO) -> dict[str, Any]:
        """Serialize a LevelResponseDTO."""
        return {
            "id": dto.id,
            "name": dto.name,
            "order": dto.order,
            "requirements": [
                RequirementResponseSerializer.from_dto(r) for r in dto.requirements
            ],
        }


class CareerPathResponseSerializer(serializers.Serializer[dict[str, Any]]):
    """Output serializer for a career path with its complete level hierarchy."""

    id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
    levels = LevelResponseSerializer(many=True)

    @classmethod
    def from_dto(cls, dto: PathResponseDTO) -> dict[str, Any]:
        """Serialize a PathResponseDTO."""
        return {
            "id": dto.id,
            "name": dto.name,
            "description": dto.description,
            "levels": [LevelResponseSerializer.from_dto(lvl) for lvl in dto.levels],
        }
