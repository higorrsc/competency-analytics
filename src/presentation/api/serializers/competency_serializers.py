"""Serializers for competency catalog endpoints."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from src.application.dto.competency_dtos import (
    CompetencyCreateDTO,
    CompetencyResponseDTO,
)


class CompetencyCreateSerializer(serializers.Serializer[dict[str, Any]]):
    """Serializer validating input for creating a competency."""

    name = serializers.CharField(max_length=200)
    description = serializers.CharField(allow_blank=True, default="")
    category_id = serializers.UUIDField()
    group_id = serializers.UUIDField()
    level_descriptions = serializers.DictField(
        child=serializers.CharField(),
        help_text="Mapping of proficiency levels 1-5 to description strings",
    )

    def validate_level_descriptions(self, value: dict[Any, Any]) -> dict[int, str]:
        """Ensure all 5 proficiency levels are present with descriptions."""
        int_keys: dict[int, str] = {}
        for k, v in value.items():
            try:
                int_k = int(k)
            except (ValueError, TypeError) as exc:
                raise serializers.ValidationError(
                    f"Level key {k!r} must be an integer between 1 and 5"
                ) from exc
            if int_k < 1 or int_k > 5:
                raise serializers.ValidationError(
                    f"Level key {int_k} out of range 1..5"
                )
            int_keys[int_k] = str(v)

        expected_levels = {1, 2, 3, 4, 5}
        if set(int_keys.keys()) != expected_levels:
            missing = expected_levels - set(int_keys.keys())
            raise serializers.ValidationError(
                f"Missing level descriptions for levels: {sorted(missing)}"
            )

        return int_keys

    def to_dto(self) -> CompetencyCreateDTO:
        """Convert validated serializer data to application DTO."""
        data = self.validated_data
        return CompetencyCreateDTO(
            name=data["name"],
            description=data.get("description", ""),
            category_id=data["category_id"],
            group_id=data["group_id"],
            level_descriptions=data["level_descriptions"],
        )


class CompetencyResponseSerializer(serializers.Serializer[dict[str, Any]]):
    """Serializer representing a stored competency with its 5 levels."""

    id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
    category_id = serializers.UUIDField()
    group_id = serializers.UUIDField()
    level_descriptions = serializers.DictField(child=serializers.CharField())

    @classmethod
    def from_dto(cls, dto: CompetencyResponseDTO) -> dict[str, Any]:
        """Serialize a CompetencyResponseDTO instance."""
        return {
            "id": dto.id,
            "name": dto.name,
            "description": dto.description,
            "category_id": dto.category_id,
            "group_id": dto.group_id,
            "level_descriptions": {
                str(k): v for k, v in dto.level_descriptions.items()
            },
        }
