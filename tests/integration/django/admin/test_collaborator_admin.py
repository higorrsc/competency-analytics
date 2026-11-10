"""Integration tests for CollaboratorAdmin and PathEnrollmentAdmin."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from django.contrib import admin
from django.test import RequestFactory

from src.infrastructure.django.admin.collaborator_admin import (
    CollaboratorAdmin,
    PathEnrollmentAdmin,
    PathEnrollmentInline,
    activate_enrollment_action,
)
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.path_enrollment import PathEnrollmentModel

NOW = datetime(2025, 1, 15, 10, 0, tzinfo=UTC)


@pytest.mark.django_db
class TestCollaboratorAdmin:
    """Tests for CollaboratorAdmin display methods, inlines, and actions."""

    def test_collaborator_admin_inlines(self) -> None:
        """CollaboratorAdmin registers PathEnrollmentInline."""
        model_admin = CollaboratorAdmin(CollaboratorModel, admin.site)
        assert PathEnrollmentInline in model_admin.inlines

    def test_active_path_display_shows_active_enrollment(self) -> None:
        """active_path_display formats the active path and target level."""
        collab = CollaboratorModel.objects.create(
            name="Tony Stark",
            email="tony@avengers.org",
            department="R&D",
        )
        path = CompetencyPathModel.objects.create(
            name="Robotics Track",
            description="",
        )
        PathEnrollmentModel.objects.create(
            collaborator=collab,
            path=path,
            target_level="Principal",
            is_active=True,
            enrolled_at=NOW,
        )

        model_admin = CollaboratorAdmin(CollaboratorModel, admin.site)
        display = model_admin.active_path_display(collab)
        assert display == "Robotics Track (Principal)"

    def test_active_path_display_handles_no_active_enrollment(self) -> None:
        """active_path_display returns fallback when no active path exists."""
        collab = CollaboratorModel.objects.create(
            name="Bruce Banner",
            email="bruce@avengers.org",
            department="Science",
        )
        model_admin = CollaboratorAdmin(CollaboratorModel, admin.site)
        assert model_admin.active_path_display(collab) == "No Active Path"

    def test_activate_enrollment_action_deactivates_other_enrollments(self) -> None:
        """activate_enrollment_action deactivates other paths for collaborator."""
        collab = CollaboratorModel.objects.create(
            name="Steve Rogers",
            email="steve@avengers.org",
            department="Tactics",
        )
        path1 = CompetencyPathModel.objects.create(
            name="Leadership Track",
            description="",
        )
        path2 = CompetencyPathModel.objects.create(
            name="Field Operations",
            description="",
        )

        enr1 = PathEnrollmentModel.objects.create(
            collaborator=collab,
            path=path1,
            target_level="Captain",
            is_active=True,
            enrolled_at=NOW,
        )
        enr2 = PathEnrollmentModel.objects.create(
            collaborator=collab,
            path=path2,
            target_level="Specialist",
            is_active=False,
            enrolled_at=NOW,
        )

        factory = RequestFactory()
        request = factory.get("/")
        model_admin = PathEnrollmentAdmin(PathEnrollmentModel, admin.site)
        model_admin.message_user = MagicMock()

        # Action: Activate enr2
        activate_enrollment_action(
            model_admin, request, PathEnrollmentModel.objects.filter(id=enr2.id)
        )

        enr1.refresh_from_db()
        enr2.refresh_from_db()

        assert enr1.is_active is False
        assert enr2.is_active is True
        model_admin.message_user.assert_called_once()
