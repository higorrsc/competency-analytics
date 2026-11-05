"""Integration tests for Django Admin configuration and custom actions."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.test.client import Client

from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.infrastructure.django.admin.category_admin import CategoryAdmin
from src.infrastructure.django.admin.collaborator_admin import (
    CollaboratorAdmin,
    PathEnrollmentAdmin,
    activate_enrollment_action,
)
from src.infrastructure.django.admin.competency_admin import CompetencyAdmin
from src.infrastructure.django.admin.competency_group_admin import (
    CompetencyGroupAdmin,
)
from src.infrastructure.django.admin.competency_path_admin import (
    CompetencyPathAdmin,
    PathLevelAdmin,
)
from src.infrastructure.django.admin.evaluation_admin import (
    CompetencyMeasurementInline,
    EvaluationAdmin,
)
from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import CompetencyGroupModel
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.evaluation import EvaluationModel
from src.infrastructure.django.models.path_enrollment import PathEnrollmentModel
from src.infrastructure.django.models.path_level import PathLevelModel

NOW = datetime(2025, 1, 15, 10, 0, tzinfo=UTC)


@pytest.fixture
def admin_user() -> User:
    """Create a superuser for admin testing."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
    )


@pytest.mark.django_db
class TestDjangoAdminRegistration:
    """Verify that all domain models are properly registered in admin.site."""

    def test_should_register_all_domain_models(self) -> None:
        """All expected infrastructure models are registered in the admin registry."""
        registered = admin.site._registry
        assert CategoryModel in registered
        assert isinstance(registered[CategoryModel], CategoryAdmin)

        assert CompetencyGroupModel in registered
        assert isinstance(registered[CompetencyGroupModel], CompetencyGroupAdmin)

        assert CompetencyModel in registered
        assert isinstance(registered[CompetencyModel], CompetencyAdmin)

        assert CompetencyPathModel in registered
        assert isinstance(registered[CompetencyPathModel], CompetencyPathAdmin)

        assert PathLevelModel in registered
        assert isinstance(registered[PathLevelModel], PathLevelAdmin)

        assert CollaboratorModel in registered
        assert isinstance(registered[CollaboratorModel], CollaboratorAdmin)

        assert PathEnrollmentModel in registered
        assert isinstance(registered[PathEnrollmentModel], PathEnrollmentAdmin)

        assert EvaluationModel in registered
        assert isinstance(registered[EvaluationModel], EvaluationAdmin)

    def test_should_allow_superuser_to_access_admin_changelists(
        self, client: Client, admin_user: User
    ) -> None:
        """Superuser can access all changelist views via HTTP GET."""
        client.force_login(admin_user)

        endpoints = [
            "/admin/competency/categorymodel/",
            "/admin/competency/competencygroupmodel/",
            "/admin/competency/competencymodel/",
            "/admin/competency/competencypathmodel/",
            "/admin/competency/collaboratormodel/",
            "/admin/competency/evaluationmodel/",
        ]
        for url in endpoints:
            response = client.get(url)
            assert response.status_code == 200, f"Failed accessing {url}"


@pytest.mark.django_db
class TestCollaboratorAdmin:
    """Tests for CollaboratorAdmin display methods and actions."""

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


@pytest.mark.django_db
class TestEvaluationAdminImmutability:
    """Verify that finalized evaluations are immutable in the admin interface."""

    def test_draft_evaluation_allows_edits_and_deletions(
        self, admin_user: User
    ) -> None:
        """Draft evaluations permit editing, measurement additions, and deletion."""
        collab = CollaboratorModel.objects.create(
            name="Natasha Romanoff",
            email="natasha@avengers.org",
            department="Intelligence",
        )
        evaluator = CollaboratorModel.objects.create(
            name="Clint Barton",
            email="clint@avengers.org",
            department="Tactics",
        )
        ev = EvaluationModel.objects.create(
            collaborator=collab,
            evaluator=evaluator,
            period="2025-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT.value,
        )

        eval_admin = EvaluationAdmin(EvaluationModel, admin.site)
        measurement_inline = CompetencyMeasurementInline(EvaluationModel, admin.site)

        factory = RequestFactory()
        request = factory.get("/")
        request.user = admin_user

        assert eval_admin.has_delete_permission(request, ev) is True
        assert eval_admin.is_finalized_display(ev) is False
        assert measurement_inline.has_change_permission(request, ev) is True
        assert measurement_inline.has_delete_permission(request, ev) is True
        assert measurement_inline.has_add_permission(request, ev) is True

    def test_finalized_evaluation_enforces_read_only_and_forbids_deletion(
        self, admin_user: User
    ) -> None:
        """Finalized evaluations are read-only and forbid deletion."""
        collab = CollaboratorModel.objects.create(
            name="Wanda Maximoff",
            email="wanda@avengers.org",
            department="Special Ops",
        )
        evaluator = CollaboratorModel.objects.create(
            name="Vision",
            email="vision@avengers.org",
            department="Analytics",
        )
        ev = EvaluationModel.objects.create(
            collaborator=collab,
            evaluator=evaluator,
            period="2025-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.ACCEPTED.value,
            submitted_at=NOW,
            response_date=NOW,
        )

        eval_admin = EvaluationAdmin(EvaluationModel, admin.site)
        measurement_inline = CompetencyMeasurementInline(EvaluationModel, admin.site)

        factory = RequestFactory()
        request = factory.get("/")
        request.user = admin_user

        assert eval_admin.has_delete_permission(request, ev) is False
        assert eval_admin.is_finalized_display(ev) is True

        readonly_fields = eval_admin.get_readonly_fields(request, ev)
        all_field_names = [f.name for f in EvaluationModel._meta.fields]
        assert set(readonly_fields) == set(all_field_names)

        assert measurement_inline.has_change_permission(request, ev) is False
        assert measurement_inline.has_delete_permission(request, ev) is False
        assert measurement_inline.has_add_permission(request, ev) is False
