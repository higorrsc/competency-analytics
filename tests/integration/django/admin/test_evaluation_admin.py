"""Integration tests for EvaluationAdmin and CompetencyMeasurementInline."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory

from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.infrastructure.django.admin.evaluation_admin import (
    CompetencyMeasurementInline,
    EvaluationAdmin,
)
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.evaluation import EvaluationModel

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
