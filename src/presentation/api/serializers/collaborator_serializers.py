"""Serializers for collaborator registration and career path enrollments."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from src.application.dto.collaborator_dtos import (
    CollaboratorCreateDTO,
    CollaboratorResponseDTO,
    EnrollmentCreateDTO,
    EnrollmentDTO,
)


class CollaboratorCreateSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for registering a new collaborator."""

    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    department = serializers.CharField(max_length=100)

    def to_dto(self) -> CollaboratorCreateDTO:
        """Convert validated serializer data to CollaboratorCreateDTO."""
        data = self.validated_data
        return CollaboratorCreateDTO(
            name=data["name"],
            email=data["email"],
            department=data["department"],
        )


class EnrollmentCreateSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for enrolling a collaborator in a career path."""

    path_id = serializers.UUIDField()
    target_level = serializers.CharField(max_length=100)

    def to_dto(self) -> EnrollmentCreateDTO:
        """Convert validated serializer data to EnrollmentCreateDTO."""
        data = self.validated_data
        return EnrollmentCreateDTO(
            path_id=data["path_id"],
            target_level=data["target_level"],
        )


class ActivatePathSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for activating an existing career path enrollment."""

    path_id = serializers.UUIDField()


class EnrollmentResponseSerializer(serializers.Serializer[dict[str, Any]]):
    """Output serializer for a single path enrollment record."""

    path_id = serializers.UUIDField()
    target_level = serializers.CharField()
    is_active = serializers.BooleanField()
    enrolled_at = serializers.DateTimeField()

    @classmethod
    def from_dto(cls, dto: EnrollmentDTO) -> dict[str, Any]:
        """Serialize an EnrollmentDTO."""
        return {
            "path_id": dto.path_id,
            "target_level": dto.target_level,
            "is_active": dto.is_active,
            "enrolled_at": dto.enrolled_at,
        }


class CollaboratorResponseSerializer(serializers.Serializer[dict[str, Any]]):
    """Output serializer for collaborator details and enrollment history."""

    id = serializers.UUIDField()
    name = serializers.CharField()
    email = serializers.CharField()
    department = serializers.CharField()
    enrollments = EnrollmentResponseSerializer(many=True)

    @classmethod
    def from_dto(cls, dto: CollaboratorResponseDTO) -> dict[str, Any]:
        """Serialize a CollaboratorResponseDTO."""
        return {
            "id": dto.id,
            "name": dto.name,
            "email": dto.email,
            "department": dto.department,
            "enrollments": [
                EnrollmentResponseSerializer.from_dto(e) for e in dto.enrollments
            ],
        }
