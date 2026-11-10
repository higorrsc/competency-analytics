"""Unit tests for collaborator DTOs."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.application.dto.collaborator import (
    CollaboratorCreateDTO,
    CollaboratorResponseDTO,
    EnrollmentCreateDTO,
    EnrollmentDTO,
)

ENROLLED_AT = datetime(2026, 1, 15, 10, 30, tzinfo=UTC)


class TestCollaboratorCreateDTO:
    """Test validation of CollaboratorCreateDTO."""

    def test_should_accept_valid_input(self) -> None:
        """A complete collaborator registration is accepted."""
        dto = CollaboratorCreateDTO(
            name="João Silva",
            email="joao.silva@company.com",
            department="Engineering",
        )

        assert dto.name == "João Silva"
        assert dto.email == "joao.silva@company.com"
        assert dto.department == "Engineering"

    def test_should_trim_text_fields(self) -> None:
        """Surrounding whitespace is removed from text fields."""
        dto = CollaboratorCreateDTO(
            name="  João Silva  ",
            email="  joao.silva@company.com  ",
            department="  Engineering  ",
        )

        assert dto.name == "João Silva"
        assert dto.email == "joao.silva@company.com"
        assert dto.department == "Engineering"

    @pytest.mark.parametrize("field", ["name", "department"])
    def test_should_reject_blank_text_fields(self, field: str) -> None:
        """Blank names and departments are rejected."""
        data = {"name": "João", "email": "joao@company.com", "department": "Eng"}
        data[field] = "   "

        with pytest.raises(ValidationError, match=field):
            CollaboratorCreateDTO(**data)  # type: ignore[arg-type]

    def test_should_reject_blank_email(self) -> None:
        """Blank emails are rejected."""
        with pytest.raises(ValidationError, match="email"):
            CollaboratorCreateDTO(name="João", email="   ", department="Engineering")

    @pytest.mark.parametrize(
        "email",
        [
            "not-an-email",
            "joao@company",
            "@company.com",
            "joao silva@company.com",
        ],
    )
    def test_should_reject_malformed_email(self, email: str) -> None:
        """Malformed emails are rejected."""
        with pytest.raises(ValidationError, match="email"):
            CollaboratorCreateDTO(name="João", email=email, department="Engineering")


class TestEnrollmentCreateDTO:
    """Test validation of EnrollmentCreateDTO."""

    def test_should_accept_valid_enrollment(self) -> None:
        """A valid enrollment target is accepted."""
        path_id = uuid4()

        dto = EnrollmentCreateDTO(path_id=path_id, target_level="Senior")

        assert dto.path_id == path_id
        assert dto.target_level == "Senior"

    def test_should_trim_target_level(self) -> None:
        """Surrounding whitespace is removed from the target level."""
        dto = EnrollmentCreateDTO(path_id=uuid4(), target_level="  Senior  ")

        assert dto.target_level == "Senior"

    def test_should_reject_blank_target_level(self) -> None:
        """A blank target level is rejected."""
        with pytest.raises(ValidationError, match="target_level"):
            EnrollmentCreateDTO(path_id=uuid4(), target_level="   ")


class TestCollaboratorResponseDTO:
    """Test mapping of CollaboratorResponseDTO."""

    def test_should_map_collaborator_with_enrollments(self) -> None:
        """Response DTOs nest enrollment DTOs from attributes."""
        enrollment = SimpleNamespace(
            path_id=uuid4(),
            target_level="Senior",
            enrolled_at=ENROLLED_AT,
            is_active=True,
        )
        entity = SimpleNamespace(
            id=uuid4(),
            name="João Silva",
            email="joao.silva@company.com",
            department="Engineering",
            enrollments=[enrollment],
        )

        dto = CollaboratorResponseDTO.model_validate(entity)

        assert dto.enrollments[0].is_active is True
        assert dto.enrollments[0].enrolled_at == ENROLLED_AT

    def test_should_map_collaborator_without_enrollments(self) -> None:
        """Collaborators may have no enrollments."""
        entity = SimpleNamespace(
            id=uuid4(),
            name="João Silva",
            email="joao.silva@company.com",
            department="Engineering",
            enrollments=[],
        )

        dto = CollaboratorResponseDTO.model_validate(entity)

        assert dto.enrollments == []

    def test_enrollment_dto_exposes_enrollment_contract(self) -> None:
        """Enrollment responses carry path, target, date, and status."""
        path_id = uuid4()

        dto = EnrollmentDTO(
            path_id=path_id,
            target_level="Senior",
            enrolled_at=ENROLLED_AT,
            is_active=False,
        )

        assert dto.path_id == path_id
        assert dto.is_active is False
