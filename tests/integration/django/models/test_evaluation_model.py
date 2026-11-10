"""Integration tests for EvaluationModel."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from django.db import IntegrityError

from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.evaluation import EvaluationModel

NOW = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)


@pytest.mark.django_db
class TestEvaluationModel:
    """
    Tests for EvaluationModel lifecycle, transitions, and immutability.
    """

    def _setup_collabs(self) -> tuple[CollaboratorModel, CollaboratorModel]:
        collab = CollaboratorModel.objects.create(
            name="Employee", email="emp@corp.com", department="Dev"
        )
        evaluator = CollaboratorModel.objects.create(
            name="Manager", email="mgr@corp.com", department="Dev"
        )
        return collab, evaluator

    def test_should_allow_updating_draft_evaluation(self) -> None:
        """Draft evaluations can be modified freely."""
        collab, evaluator = self._setup_collabs()
        evaluation = EvaluationModel.objects.create(
            collaborator=collab,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT.value,
        )

        evaluation.period = "2026-Q1-revised"
        evaluation.save()
        evaluation.refresh_from_db()
        assert evaluation.period == "2026-Q1-revised"

    def test_should_allow_transition_to_finalized(self) -> None:
        """Evaluation can transition from completed to accepted."""
        collab, evaluator = self._setup_collabs()
        evaluation = EvaluationModel.objects.create(
            collaborator=collab,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.COMPLETED.value,
        )

        evaluation.status = EvaluationStatus.ACCEPTED.value
        evaluation.response_notes = "Agreed with feedback"
        evaluation.save()
        evaluation.refresh_from_db()

        assert evaluation.status == EvaluationStatus.ACCEPTED.value

    def test_should_prevent_modifying_accepted_evaluation(self) -> None:
        """Accepted evaluation cannot be modified."""
        collab, evaluator = self._setup_collabs()
        evaluation = EvaluationModel.objects.create(
            collaborator=collab,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.ACCEPTED.value,
        )

        evaluation.period = "Modified Period"
        with pytest.raises(IntegrityError, match="Cannot modify finalized evaluation"):
            evaluation.save()

    def test_should_prevent_modifying_contested_evaluation(self) -> None:
        """Contested evaluation cannot be modified."""
        collab, evaluator = self._setup_collabs()
        evaluation = EvaluationModel.objects.create(
            collaborator=collab,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.CONTESTED.value,
            response_notes="Disagreed",
        )

        evaluation.status = EvaluationStatus.DRAFT.value
        with pytest.raises(IntegrityError, match="Cannot modify finalized evaluation"):
            evaluation.save()

    def test_should_prevent_deleting_accepted_evaluation(self) -> None:
        """Accepted evaluations cannot be deleted."""
        collab, evaluator = self._setup_collabs()
        evaluation = EvaluationModel.objects.create(
            collaborator=collab,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.ACCEPTED.value,
        )

        with pytest.raises(IntegrityError, match="Cannot delete finalized evaluation"):
            evaluation.delete()

    def test_should_prevent_deleting_contested_evaluation(self) -> None:
        """Contested evaluations cannot be deleted."""
        collab, evaluator = self._setup_collabs()
        evaluation = EvaluationModel.objects.create(
            collaborator=collab,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.CONTESTED.value,
            response_notes="Contested notes",
        )

        with pytest.raises(IntegrityError, match="Cannot delete finalized evaluation"):
            evaluation.delete()
