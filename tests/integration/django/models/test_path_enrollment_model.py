"""Integration tests for PathEnrollmentModel."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from django.db import IntegrityError

from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.path_enrollment import PathEnrollmentModel

NOW = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)


@pytest.mark.django_db
class TestPathEnrollmentModel:
    """
    Tests for PathEnrollmentModel persistence and constraints.
    """

    def test_should_create_enrollment_and_display_str(self) -> None:
        """Enrollment persists and formats active state on __str__."""
        collaborator = CollaboratorModel.objects.create(
            name="Alice", email="alice@corp.com", department="Engineering"
        )
        path = CompetencyPathModel.objects.create(name="Backend Track")
        enrollment = PathEnrollmentModel.objects.create(
            collaborator=collaborator,
            path=path,
            target_level="Senior",
            is_active=True,
            enrolled_at=NOW,
        )
        assert "Active" in str(enrollment)
        assert enrollment.target_level == "Senior"

    def test_should_enforce_unique_together_on_path_enrollment(self) -> None:
        """Collaborator cannot be enrolled in the same path multiple times."""
        collaborator = CollaboratorModel.objects.create(
            name="Charlie", email="charlie@corp.com", department="IT"
        )
        path = CompetencyPathModel.objects.create(name="DevOps")

        PathEnrollmentModel.objects.create(
            collaborator=collaborator,
            path=path,
            target_level="Junior",
            is_active=True,
            enrolled_at=NOW,
        )

        with pytest.raises(IntegrityError):
            PathEnrollmentModel.objects.create(
                collaborator=collaborator,
                path=path,
                target_level="Senior",
                is_active=False,
                enrolled_at=NOW,
            )
