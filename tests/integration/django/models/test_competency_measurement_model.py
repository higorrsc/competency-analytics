"""Integration tests for CompetencyMeasurementModel."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from django.db import IntegrityError, transaction

from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import CompetencyGroupModel
from src.infrastructure.django.models.competency_measurement import (
    CompetencyMeasurementModel,
)
from src.infrastructure.django.models.evaluation import EvaluationModel
from tests.integration.django.models.helpers import make_descriptions

NOW = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)


@pytest.mark.django_db
class TestCompetencyMeasurementModel:
    """Tests for CompetencyMeasurementModel constraints and immutability."""

    def _setup_base(
        self,
    ) -> tuple[CollaboratorModel, CollaboratorModel, CompetencyModel]:
        collaborator = CollaboratorModel.objects.create(
            name="Employee", email="emp@corp.com", department="Dev"
        )
        evaluator = CollaboratorModel.objects.create(
            name="Manager", email="mgr@corp.com", department="Dev"
        )
        category = CategoryModel.objects.create(name="Tech")
        group = CompetencyGroupModel.objects.create(category=category, name="Core")
        comp = CompetencyModel.objects.create(
            category=category,
            group=group,
            name="Python",
            description="Language",
            level_descriptions=make_descriptions(),
        )
        return collaborator, evaluator, comp

    def test_should_allow_updating_measurement_in_draft(self) -> None:
        """Measurements in draft evaluations can be updated."""
        collab, evaluator, comp = self._setup_base()
        evaluation = EvaluationModel.objects.create(
            collaborator=collab,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT.value,
        )
        measurement = CompetencyMeasurementModel.objects.create(
            evaluation=evaluation,
            competency=comp,
            current_level=3,
            notes="Initial notes",
        )

        measurement.current_level = 4
        measurement.notes = "Updated notes"
        measurement.save()
        measurement.refresh_from_db()
        assert measurement.current_level == 4

    def test_should_prevent_adding_modifying_deleting_measurements_on_finalized(
        self,
    ) -> None:
        """
        Measurements cannot be modified or deleted once evaluation is finalized.
        """
        collab, evaluator, comp = self._setup_base()
        evaluation = EvaluationModel.objects.create(
            collaborator=collab,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT.value,
        )
        measurement = CompetencyMeasurementModel.objects.create(
            evaluation=evaluation,
            competency=comp,
            current_level=3,
        )

        # Finalize evaluation
        evaluation.status = EvaluationStatus.ACCEPTED.value
        evaluation.save()

        # Try to modify existing measurement
        measurement.current_level = 5
        with pytest.raises(
            IntegrityError,
            match="Cannot modify measurements of a finalized evaluation",
        ):
            measurement.save()

        # Try to delete measurement
        with pytest.raises(
            IntegrityError,
            match="Cannot delete measurements of a finalized evaluation",
        ):
            measurement.delete()

        # Try to add a new measurement to finalized evaluation
        comp2 = CompetencyModel.objects.create(
            category=comp.category,
            group=comp.group,
            name="Docker",
            description="Containers",
            level_descriptions=make_descriptions(),
        )
        new_measurement = CompetencyMeasurementModel(
            evaluation=evaluation,
            competency=comp2,
            current_level=2,
        )
        with pytest.raises(
            IntegrityError,
            match="Cannot modify measurements of a finalized evaluation",
        ):
            new_measurement.save()

    def test_should_enforce_valid_measurement_level_range(self) -> None:
        """Measurement level must be between 1 and 5."""
        collab, evaluator, comp = self._setup_base()
        evaluation = EvaluationModel.objects.create(
            collaborator=collab,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT.value,
        )

        with transaction.atomic(), pytest.raises(IntegrityError):
            CompetencyMeasurementModel.objects.create(
                evaluation=evaluation,
                competency=comp,
                current_level=0,
            )

        with transaction.atomic(), pytest.raises(IntegrityError):
            CompetencyMeasurementModel.objects.create(
                evaluation=evaluation,
                competency=comp,
                current_level=6,
            )
