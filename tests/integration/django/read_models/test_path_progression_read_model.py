"""Integration tests for DjangoPathProgressionReadModel."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.application.ports.read_models import PathProgressionReadModel
from src.domain.entities.collaborator import Collaborator
from src.domain.entities.competency import Competency
from src.domain.entities.competency_measurement import CompetencyMeasurement
from src.domain.entities.competency_path import CompetencyPath
from src.domain.entities.evaluation import Evaluation
from src.domain.entities.path_level import PathLevel
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.competency_requirement import CompetencyRequirement
from src.domain.value_objects.evaluation_id import EvaluationId
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.domain.value_objects.group_id import GroupId
from src.domain.value_objects.level_id import LevelId
from src.domain.value_objects.measurement_id import MeasurementId
from src.domain.value_objects.path_enrollment import PathEnrollment
from src.domain.value_objects.path_id import PathId
from src.domain.value_objects.requirement_weight import RequirementWeight
from src.infrastructure.django.read_models.path_progression_read_model import (
    DjangoPathProgressionReadModel,
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
from src.infrastructure.django.repositories.path_repository import (
    DjangoPathRepository,
)

BASE_DATE = datetime(2025, 1, 15, 10, 0, tzinfo=UTC)


@pytest.mark.django_db
class TestDjangoPathProgressionReadModel:
    """Integration test suite for DjangoPathProgressionReadModel."""

    def _setup_track(
        self,
    ) -> tuple[Collaborator, Collaborator, CompetencyPath, Competency, Competency]:
        """
        Create career path with Junior level requirements and enrolled collaborator.
        """
        collab_repo = DjangoCollaboratorRepository()
        path_repo = DjangoPathRepository()
        comp_repo = DjangoCompetencyRepository()

        comp1 = Competency(
            id=CompetencyId.generate(),
            category_id=CategoryId.generate(),
            group_id=GroupId.generate(),
            name="Python",
            description="Python skills",
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
            description="SQL skills",
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

        # Career path with 2 requirements on "Junior":
        # - Python: min level 2
        # - SQL: min level 3
        path = CompetencyPath(
            id=PathId.generate(),
            name="Backend Engineering",
            description="Backend developer ladder",
            levels=[
                PathLevel(
                    id=LevelId.generate(),
                    name="Junior",
                    order=1,
                    requirements=[
                        CompetencyRequirement(
                            competency_id=comp1.id,
                            minimum_level=2,
                            weight=RequirementWeight.CORE,
                        ),
                        CompetencyRequirement(
                            competency_id=comp2.id,
                            minimum_level=3,
                            weight=RequirementWeight.CORE,
                        ),
                    ],
                )
            ],
        )
        path_repo.save(path)

        collab = Collaborator(
            id=CollaboratorId.generate(),
            name="Carol Danvers",
            email="carol@marvel.org",
            department="Engineering",
            enrollments=[
                PathEnrollment(
                    path_id=path.id,
                    target_level="Junior",
                    enrolled_at=BASE_DATE,
                    is_active=True,
                )
            ],
        )
        evaluator = Collaborator(
            id=CollaboratorId.generate(),
            name="Nick Fury",
            email="fury@shield.gov",
            department="Management",
        )
        collab_repo.save(collab)
        collab_repo.save(evaluator)

        return collab, evaluator, path, comp1, comp2

    def test_should_satisfy_progression_protocol(self) -> None:
        """Read model satisfies the PathProgressionReadModel protocol."""
        read_model = DjangoPathProgressionReadModel()
        assert isinstance(read_model, PathProgressionReadModel)

    def test_should_calculate_completion_percentage(self) -> None:
        """Calculates requirements met and percentage against target level."""
        collab, evaluator, path, comp1, comp2 = self._setup_track()
        eval_repo = DjangoEvaluationRepository()
        read_model = DjangoPathProgressionReadModel()

        # Finalized evaluation meets Python (level 2 >= 2) but fails SQL (level 2 < 3)
        ev = Evaluation(
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
                ),
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=comp2.id,
                    current_level=2,
                ),
            ],
        )
        eval_repo.save(ev)

        summary = read_model.get_progression_summary(collab.id, path.id)

        assert summary is not None
        assert summary.collaborator_id == collab.id.value
        assert summary.path_id == path.id.value
        assert summary.target_level == "Junior"
        assert summary.total_requirements == 2
        assert summary.requirements_met == 1
        assert summary.completion_percentage == 50.0

    def test_should_use_latest_finalized_evaluation(self) -> None:
        """Uses the latest finalized evaluation measurement for each competency."""
        collab, evaluator, path, comp1, comp2 = self._setup_track()
        eval_repo = DjangoEvaluationRepository()
        read_model = DjangoPathProgressionReadModel()

        # First evaluation: meets neither requirement
        ev1 = Evaluation(
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
                    current_level=1,
                ),
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=comp2.id,
                    current_level=1,
                ),
            ],
        )
        eval_repo.save(ev1)

        # Second evaluation: meets both requirements (Python 3 >= 2, SQL 3 >= 3)
        ev2 = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collab.id,
            evaluator_id=evaluator.id,
            period="2025-Q2",
            evaluation_date=BASE_DATE + timedelta(days=90),
            status=EvaluationStatus.CONTESTED,
            submitted_at=BASE_DATE + timedelta(days=90),
            response_date=BASE_DATE + timedelta(days=90),
            response_notes="Contested score",
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=comp1.id,
                    current_level=3,
                ),
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=comp2.id,
                    current_level=3,
                ),
            ],
        )
        eval_repo.save(ev2)

        summary = read_model.get_progression_summary(collab.id, path.id)

        assert summary is not None
        assert summary.requirements_met == 2
        assert summary.total_requirements == 2
        assert summary.completion_percentage == 100.0

    def test_should_return_none_when_no_finalized_evaluation(self) -> None:
        """Returns None if collaborator has only draft evaluations."""
        collab, evaluator, path, comp1, _comp2 = self._setup_track()
        eval_repo = DjangoEvaluationRepository()
        read_model = DjangoPathProgressionReadModel()

        draft = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collab.id,
            evaluator_id=evaluator.id,
            period="DRAFT-1",
            evaluation_date=BASE_DATE,
            status=EvaluationStatus.DRAFT,
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=comp1.id,
                    current_level=5,
                )
            ],
        )
        eval_repo.save(draft)

        summary = read_model.get_progression_summary(collab.id, path.id)
        assert summary is None

    def test_should_return_none_when_enrollment_is_inactive(self) -> None:
        """Returns None if collaborator enrollment in path is inactive."""
        collab_repo = DjangoCollaboratorRepository()
        path_repo = DjangoPathRepository()
        comp_repo = DjangoCompetencyRepository()
        eval_repo = DjangoEvaluationRepository()
        read_model = DjangoPathProgressionReadModel()

        comp = Competency(
            id=CompetencyId.generate(),
            category_id=CategoryId.generate(),
            group_id=GroupId.generate(),
            name="Leadership",
            description="Leading teams",
            level_descriptions={1: "L1", 2: "L2", 3: "L3", 4: "L4", 5: "L5"},
        )
        comp_repo.save(comp)

        path = CompetencyPath(
            id=PathId.generate(),
            name="Leadership Track",
            description="",
            levels=[
                PathLevel(
                    id=LevelId.generate(),
                    name="Team Lead",
                    order=1,
                    requirements=[
                        CompetencyRequirement(
                            competency_id=comp.id,
                            minimum_level=2,
                            weight=RequirementWeight.CORE,
                        )
                    ],
                )
            ],
        )
        path_repo.save(path)

        collab = Collaborator(
            id=CollaboratorId.generate(),
            name="Clark Kent",
            email="clark@dailyplanet.com",
            department="Editorial",
            enrollments=[
                PathEnrollment(
                    path_id=path.id,
                    target_level="Team Lead",
                    enrolled_at=BASE_DATE,
                    is_active=False,  # Inactive enrollment
                )
            ],
        )
        evaluator = Collaborator(
            id=CollaboratorId.generate(),
            name="Perry White",
            email="perry@dailyplanet.com",
            department="Editorial",
        )
        collab_repo.save(collab)
        collab_repo.save(evaluator)

        ev = Evaluation(
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
                    competency_id=comp.id,
                    current_level=3,
                )
            ],
        )
        eval_repo.save(ev)

        summary = read_model.get_progression_summary(collab.id, path.id)
        assert summary is None
