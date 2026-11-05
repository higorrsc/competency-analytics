"""Unit tests for the calculate competency gaps use case."""

from datetime import UTC, datetime

import pytest

from src.application.dto.gap_analysis_dtos import GapAnalysisRequestDTO
from src.application.use_cases.errors import NotFoundError
from src.application.use_cases.gap_analysis_use_cases import (
    CalculateCompetencyGapsUseCase,
)
from src.domain.entities.collaborator import Collaborator
from src.domain.entities.competency import Competency
from src.domain.entities.competency_measurement import CompetencyMeasurement
from src.domain.entities.competency_path import CompetencyPath
from src.domain.entities.evaluation import Evaluation
from src.domain.entities.path_level import PathLevel
from src.domain.services.gap_analysis_service import GapAnalysisService
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.collaborator_id import CollaboratorId as CollaboratorIdVo
from src.domain.value_objects.competency_id import CompetencyId as CompetencyIdVo
from src.domain.value_objects.competency_requirement import CompetencyRequirement
from src.domain.value_objects.evaluation_id import EvaluationId as EvaluationIdVo
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.domain.value_objects.group_id import GroupId
from src.domain.value_objects.level_id import LevelId as LevelIdVo
from src.domain.value_objects.measurement_id import MeasurementId
from src.domain.value_objects.path_id import PathId as PathIdVo
from src.domain.value_objects.requirement_weight import RequirementWeight
from tests.unit.application.use_cases.fakes import (
    FakeEvaluationRepository,
    FakePathRepository,
)

EVALUATION_DATE = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)

LEVEL_DESCRIPTIONS = {
    1: "None",
    2: "Basic",
    3: "Good",
    4: "Strong",
    5: "Expert",
}


def make_competency(name: str) -> Competency:
    """Build a valid stored competency."""
    return Competency(
        id=CompetencyIdVo.generate(),
        name=name,
        description="Programming language",
        category_id=CategoryId.generate(),
        group_id=GroupId.generate(),
        level_descriptions=LEVEL_DESCRIPTIONS,
    )


def make_collaborator() -> Collaborator:
    """Build a valid stored collaborator."""
    return Collaborator(
        id=CollaboratorIdVo.generate(),
        name="João Silva",
        email="joao.silva@company.com",
        department="Engineering",
    )


class GapAnalysisWorld:
    """Fixture container wiring repositories, entities, and the use case."""

    def __init__(self) -> None:
        """Create competencies, path, level, and repositories."""
        self.python = make_competency("Python")
        self.testing = make_competency("Testing")
        self.level = PathLevel(
            id=LevelIdVo.generate(),
            name="Senior",
            order=1,
        )
        self.level.add_requirement(
            CompetencyRequirement(
                competency_id=self.python.id,
                minimum_level=4,
                weight=RequirementWeight.CORE,
            )
        )
        self.level.add_requirement(
            CompetencyRequirement(
                competency_id=self.testing.id,
                minimum_level=3,
                weight=RequirementWeight.IMPORTANT,
            )
        )
        self.path = CompetencyPath(
            id=PathIdVo.generate(),
            name="Software Engineer Track",
            description="Progression",
        )
        self.path.add_level(self.level)
        self.path_repository = FakePathRepository()
        self.path_repository.save(self.path)
        self.evaluation_repository = FakeEvaluationRepository()
        self.use_case = CalculateCompetencyGapsUseCase(
            self.evaluation_repository,
            self.path_repository,
            GapAnalysisService(),
        )

    def add_finalized_evaluation(
        self,
        levels: dict[CompetencyIdVo, int],
        status: EvaluationStatus = EvaluationStatus.ACCEPTED,
    ) -> Evaluation:
        """Create and store a finalized evaluation with the given levels."""
        collaborator = make_collaborator()
        evaluation = Evaluation(
            id=EvaluationIdVo.generate(),
            collaborator_id=collaborator.id,
            evaluator_id=make_collaborator().id,
            period="Q1 2026",
            evaluation_date=EVALUATION_DATE,
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=competency_id,
                    current_level=current_level,
                )
                for competency_id, current_level in levels.items()
            ],
            submitted_at=datetime(2026, 4, 2, 9, 0, tzinfo=UTC),
            status=status,
            response_date=datetime(2026, 4, 3, 9, 0, tzinfo=UTC),
            response_notes="Okay",
        )
        self.evaluation_repository.save(evaluation)
        return evaluation

    def request(self, evaluation: Evaluation) -> GapAnalysisRequestDTO:
        """Build a request DTO pointing at the path level."""
        return GapAnalysisRequestDTO(
            collaborator_id=evaluation.collaborator_id.value,
            path_id=self.path.id.value,
            level_id=self.level.id.value,
        )


class TestCalculateCompetencyGapsUseCase:
    """Test orchestration of CalculateCompetencyGapsUseCase."""

    def test_should_return_prioritized_gaps_and_eligibility(self) -> None:
        """Gaps are mapped with CORE blockers surfacing eligibility."""
        world = GapAnalysisWorld()
        # Python measured at 2 (CORE gap of 2), Testing measured at 5 (no gap).
        evaluation = world.add_finalized_evaluation(
            {world.python.id: 2, world.testing.id: 5}
        )

        response = world.use_case.execute(world.request(evaluation))

        assert [gap.gap for gap in response.gaps] == [2, 0]
        assert response.gaps[0].competency_id == world.python.id.value
        assert response.gaps[0].required_level == 4
        assert response.gaps[0].weight.value == "CORE"
        assert response.eligibility.is_eligible is False

    def test_should_treat_unmeasured_competency_as_full_gap(self) -> None:
        """An unmeasured competency produces a full gap from level 0."""
        world = GapAnalysisWorld()
        evaluation = world.add_finalized_evaluation({world.python.id: 4})

        response = world.use_case.execute(world.request(evaluation))

        unmeasured = next(
            gap for gap in response.gaps if gap.competency_id == world.testing.id.value
        )
        assert unmeasured.current_level == 0
        assert unmeasured.gap == 3

    def test_should_be_eligible_when_no_core_gaps_remain(self) -> None:
        """Meeting all CORE requirements yields eligibility."""
        world = GapAnalysisWorld()
        evaluation = world.add_finalized_evaluation(
            {world.python.id: 5, world.testing.id: 2}
        )

        response = world.use_case.execute(world.request(evaluation))

        assert response.eligibility.is_eligible is True
        assert response.eligibility.blocking_competency_ids == []

    def test_should_work_with_contested_baseline(self) -> None:
        """CONTESTED evaluations are valid final baselines."""
        world = GapAnalysisWorld()
        evaluation = world.add_finalized_evaluation(
            {world.python.id: 4, world.testing.id: 5},
            status=EvaluationStatus.CONTESTED,
        )

        response = world.use_case.execute(world.request(evaluation))

        assert response.eligibility.is_eligible is True

    def test_should_reject_when_collaborator_has_no_finalized_evaluation(
        self,
    ) -> None:
        """Draft and submitted evaluations are not valid baselines."""
        world = GapAnalysisWorld()
        # The world has no evaluation at all: nothing to analyze.
        request = GapAnalysisRequestDTO(
            collaborator_id=CollaboratorIdVo.generate().value,
            path_id=world.path.id.value,
            level_id=world.level.id.value,
        )

        with pytest.raises(NotFoundError, match="Finalized evaluation"):
            world.use_case.execute(request)

    def test_should_reject_when_only_draft_evaluation_exists(self) -> None:
        """A draft evaluation is not accepted as an analysis baseline."""
        world = GapAnalysisWorld()
        collaborator = make_collaborator()
        world.evaluation_repository.save(
            Evaluation(
                id=EvaluationIdVo.generate(),
                collaborator_id=collaborator.id,
                evaluator_id=make_collaborator().id,
                period="Q1 2026",
                evaluation_date=EVALUATION_DATE,
            )
        )
        request = GapAnalysisRequestDTO(
            collaborator_id=collaborator.id.value,
            path_id=world.path.id.value,
            level_id=world.level.id.value,
        )

        with pytest.raises(NotFoundError, match="Finalized evaluation"):
            world.use_case.execute(request)

    def test_should_reject_unknown_path(self) -> None:
        """The analyzed path must exist."""
        world = GapAnalysisWorld()
        evaluation = world.add_finalized_evaluation(
            {world.python.id: 4, world.testing.id: 3}
        )

        with pytest.raises(NotFoundError, match="Path"):
            world.use_case.execute(
                GapAnalysisRequestDTO(
                    collaborator_id=evaluation.collaborator_id.value,
                    path_id=PathIdVo.generate().value,
                    level_id=world.level.id.value,
                )
            )

    def test_should_reject_unknown_level(self) -> None:
        """The analyzed level must belong to the path."""
        world = GapAnalysisWorld()
        evaluation = world.add_finalized_evaluation(
            {world.python.id: 4, world.testing.id: 3}
        )

        with pytest.raises(NotFoundError, match="Path level"):
            world.use_case.execute(
                GapAnalysisRequestDTO(
                    collaborator_id=evaluation.collaborator_id.value,
                    path_id=world.path.id.value,
                    level_id=LevelIdVo.generate().value,
                )
            )
