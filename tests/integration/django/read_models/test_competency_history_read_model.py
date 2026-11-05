"""Integration tests for DjangoCompetencyHistoryReadModel."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from src.application.ports.read_models import CompetencyHistoryReadModel
from src.domain.entities.collaborator import Collaborator
from src.domain.entities.competency import Competency
from src.domain.entities.competency_measurement import CompetencyMeasurement
from src.domain.entities.evaluation import Evaluation
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.evaluation_id import EvaluationId
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.domain.value_objects.group_id import GroupId
from src.domain.value_objects.measurement_id import MeasurementId
from src.infrastructure.django.read_models.competency_history_read_model import (
    DjangoCompetencyHistoryReadModel,
)
from src.infrastructure.django.repositories.collaborator_repository import (
    DjangoCollaboratorRepository,
)
from src.infrastructure.django.repositories.competency_repository import (
    DjangoCompetencyRepository,
)
from src.infrastructure.django.repositories.evaluation_repository import (
    DjangoEvaluationRepository,
)

BASE_DATE = datetime(2025, 1, 15, 10, 0, tzinfo=UTC)


@pytest.mark.django_db
class TestDjangoCompetencyHistoryReadModel:
    """Integration test suite for DjangoCompetencyHistoryReadModel."""

    def _setup_baseline(
        self,
    ) -> tuple[Collaborator, Collaborator, Competency, Competency]:
        """Create collaborator, evaluator, and two competencies."""
        collab_repo = DjangoCollaboratorRepository()
        comp_repo = DjangoCompetencyRepository()

        collab = Collaborator(
            id=CollaboratorId.generate(),
            name="Alice Smith",
            email="alice.smith@example.com",
            department="Engineering",
        )
        evaluator = Collaborator(
            id=CollaboratorId.generate(),
            name="Bob Lead",
            email="bob.lead@example.com",
            department="Engineering",
        )
        collab_repo.save(collab)
        collab_repo.save(evaluator)

        comp1 = Competency(
            id=CompetencyId.generate(),
            category_id=CategoryId.generate(),
            group_id=GroupId.generate(),
            name="Python",
            description="Core language skills",
            level_descriptions={
                1: "Basics",
                2: "Intermediate",
                3: "Advanced",
                4: "Expert",
                5: "Principal",
            },
        )
        comp2 = Competency(
            id=CompetencyId.generate(),
            category_id=comp1.category_id,
            group_id=comp1.group_id,
            name="SQL",
            description="Relational database querying",
            level_descriptions={
                1: "Queries",
                2: "Joins",
                3: "Indexing",
                4: "Optimization",
                5: "Internals",
            },
        )
        comp_repo.save(comp1)
        comp_repo.save(comp2)

        return collab, evaluator, comp1, comp2

    def test_should_satisfy_history_protocol(self) -> None:
        """Read model satisfies the CompetencyHistoryReadModel protocol."""
        read_model = DjangoCompetencyHistoryReadModel()
        assert isinstance(read_model, CompetencyHistoryReadModel)

    def test_should_query_competency_history_with_level_changes(self) -> None:
        """
        History returns chronological measurements with previous level and changes.
        """
        collab, evaluator, comp1, _comp2 = self._setup_baseline()
        eval_repo = DjangoEvaluationRepository()
        read_model = DjangoCompetencyHistoryReadModel()

        # Evaluation 1: Q1 2025 (Level 2)
        eval1 = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collab.id,
            evaluator_id=evaluator.id,
            period="2025-Q1",
            evaluation_date=BASE_DATE,
            status=EvaluationStatus.ACCEPTED,
            submitted_at=BASE_DATE,
            response_date=BASE_DATE,
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=comp1.id,
                    current_level=2,
                )
            ],
        )
        eval_repo.save(eval1)

        # Evaluation 2: Q2 2025 (Level 3 - improvement +1)
        eval2 = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collab.id,
            evaluator_id=evaluator.id,
            period="2025-Q2",
            evaluation_date=BASE_DATE + timedelta(days=90),
            status=EvaluationStatus.ACCEPTED,
            submitted_at=BASE_DATE + timedelta(days=90),
            response_date=BASE_DATE + timedelta(days=90),
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=comp1.id,
                    current_level=3,
                )
            ],
        )
        eval_repo.save(eval2)

        # Evaluation 3: Q3 2025 (Level 5 - improvement +2, contested)
        eval3 = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collab.id,
            evaluator_id=evaluator.id,
            period="2025-Q3",
            evaluation_date=BASE_DATE + timedelta(days=180),
            status=EvaluationStatus.CONTESTED,
            submitted_at=BASE_DATE + timedelta(days=180),
            response_date=BASE_DATE + timedelta(days=180),
            response_notes="Contested score",
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=comp1.id,
                    current_level=5,
                )
            ],
        )
        eval_repo.save(eval3)

        history = read_model.get_history(collab.id)

        assert len(history) == 3
        # First measurement: previous_level and level_change must be None
        assert history[0].period == "2025-Q1"
        assert history[0].current_level == 2
        assert history[0].previous_level is None
        assert history[0].level_change is None
        assert history[0].status == EvaluationStatus.ACCEPTED

        # Second measurement: improved from 2 to 3 (+1)
        assert history[1].period == "2025-Q2"
        assert history[1].current_level == 3
        assert history[1].previous_level == 2
        assert history[1].level_change == 1
        assert history[1].status == EvaluationStatus.ACCEPTED

        # Third measurement: improved from 3 to 5 (+2), contested status
        assert history[2].period == "2025-Q3"
        assert history[2].current_level == 5
        assert history[2].previous_level == 3
        assert history[2].level_change == 2
        assert history[2].status == EvaluationStatus.CONTESTED

    def test_should_filter_history_by_competency_id(self) -> None:
        """Query can be filtered to a specific competency."""
        collab, evaluator, comp1, comp2 = self._setup_baseline()
        eval_repo = DjangoEvaluationRepository()
        read_model = DjangoCompetencyHistoryReadModel()

        eval1 = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collab.id,
            evaluator_id=evaluator.id,
            period="2025-Q1",
            evaluation_date=BASE_DATE,
            status=EvaluationStatus.ACCEPTED,
            submitted_at=BASE_DATE,
            response_date=BASE_DATE,
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=comp1.id,
                    current_level=3,
                ),
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=comp2.id,
                    current_level=4,
                ),
            ],
        )
        eval_repo.save(eval1)

        history_comp1 = read_model.get_history(collab.id, competency_id=comp1.id)
        assert len(history_comp1) == 1
        assert history_comp1[0].competency_id == comp1.id.value
        assert history_comp1[0].competency_name == "Python"

        history_comp2 = read_model.get_history(collab.id, competency_id=comp2.id)
        assert len(history_comp2) == 1
        assert history_comp2[0].competency_id == comp2.id.value
        assert history_comp2[0].competency_name == "SQL"

    def test_should_filter_history_by_date_range(self) -> None:
        """Query respects start_date and end_date filters."""
        collab, evaluator, comp1, _comp2 = self._setup_baseline()
        eval_repo = DjangoEvaluationRepository()
        read_model = DjangoCompetencyHistoryReadModel()

        dates = [
            BASE_DATE,  # Jan 15 2025
            BASE_DATE + timedelta(days=60),  # Mar 16 2025
            BASE_DATE + timedelta(days=120),  # May 15 2025
        ]

        for i, dt in enumerate(dates):
            ev = Evaluation(
                id=EvaluationId.generate(),
                collaborator_id=collab.id,
                evaluator_id=evaluator.id,
                period=f"P{i + 1}",
                evaluation_date=dt,
                status=EvaluationStatus.ACCEPTED,
                submitted_at=dt,
                response_date=dt,
                measurements=[
                    CompetencyMeasurement(
                        id=MeasurementId.generate(),
                        competency_id=comp1.id,
                        current_level=i + 1,
                    )
                ],
            )
            eval_repo.save(ev)

        # Filter strictly to March
        filtered = read_model.get_history(
            collab.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
        )
        assert len(filtered) == 1
        assert filtered[0].period == "P2"

        # Filter start_date only
        from_march = read_model.get_history(
            collab.id,
            start_date=date(2025, 3, 1),
        )
        assert len(from_march) == 2
        assert [e.period for e in from_march] == ["P2", "P3"]

        # Filter end_date only
        until_feb = read_model.get_history(
            collab.id,
            end_date=date(2025, 2, 1),
        )
        assert len(until_feb) == 1
        assert until_feb[0].period == "P1"

    def test_should_exclude_draft_and_completed_evaluations(self) -> None:
        """Views include only finalized evaluations (ACCEPTED and CONTESTED)."""
        collab, evaluator, comp1, _comp2 = self._setup_baseline()
        eval_repo = DjangoEvaluationRepository()
        read_model = DjangoCompetencyHistoryReadModel()

        # DRAFT evaluation
        draft = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collab.id,
            evaluator_id=evaluator.id,
            period="DRAFT-Q1",
            evaluation_date=BASE_DATE,
            status=EvaluationStatus.DRAFT,
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=comp1.id,
                    current_level=1,
                )
            ],
        )
        eval_repo.save(draft)

        # COMPLETED evaluation
        completed = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collab.id,
            evaluator_id=evaluator.id,
            period="COMPL-Q1",
            evaluation_date=BASE_DATE + timedelta(days=10),
            status=EvaluationStatus.COMPLETED,
            submitted_at=BASE_DATE + timedelta(days=10),
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=comp1.id,
                    current_level=2,
                )
            ],
        )
        eval_repo.save(completed)

        history = read_model.get_history(collab.id)
        assert len(history) == 0
