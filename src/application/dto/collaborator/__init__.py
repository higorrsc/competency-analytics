"""Collaborator application DTOs."""

from src.application.dto.collaborator.requests import (
    CollaboratorCreateDTO,
    EnrollmentCreateDTO,
)
from src.application.dto.collaborator.responses import (
    CollaboratorResponseDTO,
    EnrollmentDTO,
)

__all__ = [
    "CollaboratorCreateDTO",
    "CollaboratorResponseDTO",
    "EnrollmentCreateDTO",
    "EnrollmentDTO",
]
