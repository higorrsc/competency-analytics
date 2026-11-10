"""Integration tests for DjangoEvaluationRepository."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.domain.entities.collaborator import Collaborator
from src.domain.entities.competency import Competency
from src.domain.entities.competency_measurement import CompetencyMeasurement
from src.domain.entities.evaluation import Evaluation
from src.domain.repositories.evaluation_repository import EvaluationRepository
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.evaluation_id import EvaluationId
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.domain.value_objects.measurement_id import MeasurementId
from src.infrastructure.django.repositories.collaborator_repository import (
    DjangoCollaboratorRepository,
)
from src.infrastructure.django.repositories.competency_repository import (
    DjangoCompetencyRepository,
)
from src.infrastructure.django.repositories.evaluation_repository import (
    DjangoEvaluationRepository,
)
from tests.integration.django.repositories.helpers import make_competency

NOW = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)


@pytest.mark.django_db
class TestDjangoEvaluationRepository:
    """Tests for DjangoEvaluationRepository implementing EvaluationRepository."""

    def _setup_collabs_and_comp(
        self,
    ) -> tuple[Collaborator, Collaborator, Competency]:
        collab_repo = DjangoCollaboratorRepository()
        comp_repo = DjangoCompetencyRepository()

        collaborator = Collaborator(
            id=CollaboratorId.generate(),
            name="John Doe",
            email="john@corp.com",
            department="Engineering",
        )
        evaluator = Collaborator(
            id=CollaboratorId.generate(),
            name="Jane Boss",
            email="jane@corp.com",
            department="Engineering",
        )
        collab_repo.save(collaborator)
        collab_repo.save(evaluator)

        competency = make_competency()
        comp_repo.save(competency)
        return collaborator, evaluator, competency

    def test_should_satisfy_protocol(self) -> None:
        """Repository satisfies the domain protocol."""
        repo = DjangoEvaluationRepository()
        assert isinstance(repo, EvaluationRepository)

    def test_should_save_and_retrieve_evaluation_with_measurements(self) -> None:
        """Evaluation aggregate persists with measurements and dates."""
        collaborator, evaluator, competency = self._setup_collabs_and_comp()
        repo = DjangoEvaluationRepository()

        measurement = CompetencyMeasurement(
            id=MeasurementId.generate(),
            competency_id=competency.id,
            current_level=3,
            notes="Strong skills",
            evidence="PR #42",
        )
        evaluation = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collaborator.id,
            evaluator_id=evaluator.id,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT,
            measurements=[measurement],
        )

        repo.save(evaluation)
        loaded = repo.get_by_id(evaluation.id)

        assert loaded is not None
        assert isinstance(loaded, Evaluation)
        assert loaded.id == evaluation.id
        assert loaded.collaborator_id == collaborator.id
        assert loaded.evaluator_id == evaluator.id
        assert loaded.period == "2026-Q1"
        assert loaded.status == EvaluationStatus.DRAFT
        assert len(loaded.measurements) == 1
        assert loaded.measurements[0].competency_id == competency.id
        assert loaded.measurements[0].current_level == 3
        assert loaded.measurements[0].notes == "Strong skills"
        assert loaded.measurements[0].evidence == "PR #42"

    def test_should_find_latest_finalized_for_collaborator(self) -> None:
        """Queries the most recent finalized evaluation, ignoring drafts."""
        collaborator, evaluator, competency = self._setup_collabs_and_comp()
        repo = DjangoEvaluationRepository()

        # Older accepted evaluation
        older = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collaborator.id,
            evaluator_id=evaluator.id,
            period="2025-Q3",
            evaluation_date=NOW - timedelta(days=180),
            status=EvaluationStatus.ACCEPTED,
            submitted_at=NOW - timedelta(days=180),
            response_date=NOW - timedelta(days=175),
            response_notes="Agreed",
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=competency.id,
                    current_level=2,
                )
            ],
        )

        # Newer contested evaluation
        newer = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collaborator.id,
            evaluator_id=evaluator.id,
            period="2025-Q4",
            evaluation_date=NOW - timedelta(days=90),
            status=EvaluationStatus.CONTESTED,
            submitted_at=NOW - timedelta(days=90),
            response_date=NOW - timedelta(days=85),
            response_notes="Disagreed with grade",
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=competency.id,
                    current_level=3,
                )
            ],
        )

        # Even newer draft evaluation (must be ignored)
        draft = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collaborator.id,
            evaluator_id=evaluator.id,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT,
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=competency.id,
                    current_level=4,
                )
            ],
        )

        repo.save(older)
        repo.save(newer)
        repo.save(draft)

        latest = repo.find_latest_finalized_for_collaborator(collaborator.id)
        assert latest is not None
        assert latest.id == newer.id
        assert latest.period == "2025-Q4"
        assert latest.status == EvaluationStatus.CONTESTED

    def test_should_return_none_when_no_finalized_evaluation_exists(
        self,
    ) -> None:
        """Returns None if collaborator only has drafts or completed evaluations."""
        collaborator, evaluator, _comp = self._setup_collabs_and_comp()
        repo = DjangoEvaluationRepository()

        draft = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collaborator.id,
            evaluator_id=evaluator.id,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT,
        )
        repo.save(draft)

        assert repo.find_latest_finalized_for_collaborator(collaborator.id) is None
