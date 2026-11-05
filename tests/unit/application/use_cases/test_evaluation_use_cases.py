"""Unit tests for the evaluation lifecycle use cases."""

from datetime import UTC, datetime

import pytest

from src.application.dto.evaluation_dtos import (
    EvaluationCreateDTO,
    MeasurementCreateDTO,
)
from src.application.use_cases.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.application.use_cases.evaluation_use_cases import (
    AcceptEvaluationUseCase,
    AddMeasurementToEvaluationUseCase,
    ContestEvaluationUseCase,
    CreateEvaluationUseCase,
    SubmitEvaluationUseCase,
)
from src.domain.entities.collaborator import Collaborator
from src.domain.entities.competency import Competency
from src.domain.entities.evaluation import Evaluation
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.collaborator_id import CollaboratorId as CollaboratorIdVo
from src.domain.value_objects.competency_id import CompetencyId as CompetencyIdVo
from src.domain.value_objects.evaluation_id import EvaluationId as EvaluationIdVo
from src.domain.value_objects.group_id import GroupId
from tests.unit.application.use_cases.fakes import (
    FakeCollaboratorRepository,
    FakeCompetencyRepository,
    FakeEvaluationRepository,
)

EVALUATION_DATE = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)

LEVEL_DESCRIPTIONS = {
    1: "None",
    2: "Basic",
    3: "Good",
    4: "Strong",
    5: "Expert",
}


def make_collaborator() -> Collaborator:
    """Build a valid stored collaborator."""
    return Collaborator(
        id=CollaboratorIdVo.generate(),
        name="João Silva",
        email="joao.silva@company.com",
        department="Engineering",
    )


def make_competency() -> Competency:
    """Build a valid stored competency."""
    return Competency(
        id=CompetencyIdVo.generate(),
        name="Python",
        description="Programming language",
        category_id=CategoryId.generate(),
        group_id=GroupId.generate(),
        level_descriptions=LEVEL_DESCRIPTIONS,
    )


def make_evaluation(
    collaborator_id: CollaboratorIdVo,
    evaluator_id: CollaboratorIdVo,
    repository: FakeEvaluationRepository,
) -> Evaluation:
    """Build and store a draft evaluation owned by ``collaborator_id``."""
    evaluation = Evaluation(
        id=EvaluationIdVo.generate(),
        collaborator_id=collaborator_id,
        evaluator_id=evaluator_id,
        period="Q1 2026",
        evaluation_date=EVALUATION_DATE,
    )
    repository.save(evaluation)
    return evaluation


def make_evaluation_dto() -> EvaluationCreateDTO:
    """Build a valid evaluation creation DTO."""
    return EvaluationCreateDTO(
        collaborator_id=CollaboratorIdVo.generate().value,
        evaluator_id=CollaboratorIdVo.generate().value,
        period="Q1 2026",
        evaluation_date=EVALUATION_DATE,
    )


class TestCreateEvaluationUseCase:
    """Test orchestration of CreateEvaluationUseCase."""

    def test_should_create_draft_evaluation_for_known_parties(self) -> None:
        """A valid draft is created and persisted."""
        evaluation_repository = FakeEvaluationRepository()
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        evaluator = make_collaborator()
        collaborator_repository.save(collaborator)
        collaborator_repository.save(evaluator)
        use_case = CreateEvaluationUseCase(
            evaluation_repository, collaborator_repository
        )

        response = use_case.execute(
            EvaluationCreateDTO(
                collaborator_id=collaborator.id.value,
                evaluator_id=evaluator.id.value,
                period="Q1 2026",
                evaluation_date=EVALUATION_DATE,
            )
        )

        assert response.status.value == "DRAFT"
        assert response.measurements == []
        assert evaluation_repository.get_by_id(EvaluationIdVo(response.id)) is not None

    def test_should_reject_unknown_collaborator(self) -> None:
        """The evaluated collaborator must exist."""
        collaborator_repository = FakeCollaboratorRepository()
        evaluator = make_collaborator()
        collaborator_repository.save(evaluator)
        use_case = CreateEvaluationUseCase(
            FakeEvaluationRepository(), collaborator_repository
        )

        with pytest.raises(NotFoundError, match="Collaborator"):
            use_case.execute(
                EvaluationCreateDTO(
                    collaborator_id=CollaboratorIdVo.generate().value,
                    evaluator_id=evaluator.id.value,
                    period="Q1 2026",
                    evaluation_date=EVALUATION_DATE,
                )
            )

    def test_should_reject_unknown_evaluator(self) -> None:
        """The evaluator must exist."""
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        collaborator_repository.save(collaborator)
        use_case = CreateEvaluationUseCase(
            FakeEvaluationRepository(), collaborator_repository
        )

        with pytest.raises(NotFoundError, match="Evaluator"):
            use_case.execute(
                EvaluationCreateDTO(
                    collaborator_id=collaborator.id.value,
                    evaluator_id=CollaboratorIdVo.generate().value,
                    period="Q1 2026",
                    evaluation_date=EVALUATION_DATE,
                )
            )


class TestAddMeasurementToEvaluationUseCase:
    """Test orchestration of AddMeasurementToEvaluationUseCase."""

    def _prepare(
        self,
    ) -> tuple[
        AddMeasurementToEvaluationUseCase,
        Evaluation,
        Competency,
        FakeEvaluationRepository,
    ]:
        """Create the collaborators, competency, and draft evaluation."""
        evaluation_repository = FakeEvaluationRepository()
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        evaluator = make_collaborator()
        collaborator_repository.save(collaborator)
        collaborator_repository.save(evaluator)
        competency_repository = FakeCompetencyRepository()
        competency = make_competency()
        competency_repository.save(competency)
        evaluation = make_evaluation(
            collaborator.id, evaluator.id, evaluation_repository
        )
        use_case = AddMeasurementToEvaluationUseCase(
            evaluation_repository, competency_repository
        )
        return use_case, evaluation, competency, evaluation_repository

    def test_should_add_measurement_to_draft(self) -> None:
        """A measurement valid against the catalog is added."""
        use_case, evaluation, competency, repository = self._prepare()

        response = use_case.execute(
            evaluation.id,
            MeasurementCreateDTO(
                competency_id=competency.id.value,
                current_level=4,
                notes="Strong skills",
            ),
        )

        assert len(response.measurements) == 1
        assert response.measurements[0].competency_id == competency.id.value
        assert response.measurements[0].current_level == 4
        stored = repository.get_by_id(evaluation.id)
        assert stored is not None
        assert len(stored.measurements) == 1

    def test_should_reject_measurement_for_unknown_competency(self) -> None:
        """Measured competencies must exist in the catalog."""
        use_case, evaluation, _, _ = self._prepare()

        with pytest.raises(NotFoundError, match="Competency"):
            use_case.execute(
                evaluation.id,
                MeasurementCreateDTO(
                    competency_id=CompetencyIdVo.generate().value,
                    current_level=3,
                ),
            )

    def test_should_reject_measurement_on_submitted_evaluation(self) -> None:
        """Submitted evaluations are immutable for measurement."""
        use_case, evaluation, competency, repository = self._prepare()
        use_case.execute(
            evaluation.id,
            MeasurementCreateDTO(competency_id=competency.id.value, current_level=3),
        )
        evaluation.submit()
        repository.save(evaluation)

        with pytest.raises(ConflictError, match="immutable"):
            use_case.execute(
                evaluation.id,
                MeasurementCreateDTO(
                    competency_id=competency.id.value, current_level=3
                ),
            )

    def test_should_reject_duplicate_competency_measurement(self) -> None:
        """Each competency may be measured only once per evaluation."""
        use_case, evaluation, competency, _ = self._prepare()
        use_case.execute(
            evaluation.id,
            MeasurementCreateDTO(competency_id=competency.id.value, current_level=3),
        )

        with pytest.raises(ConflictError, match="already contains"):
            use_case.execute(
                evaluation.id,
                MeasurementCreateDTO(
                    competency_id=competency.id.value, current_level=4
                ),
            )


class TestSubmitEvaluationUseCase:
    """Test orchestration of SubmitEvaluationUseCase."""

    def _prepare(
        self,
    ) -> tuple[SubmitEvaluationUseCase, Evaluation, FakeEvaluationRepository]:
        """Create a draft evaluation with one measurement attached."""
        evaluation_repository = FakeEvaluationRepository()
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        evaluator = make_collaborator()
        collaborator_repository.save(collaborator)
        collaborator_repository.save(evaluator)
        competency_repository = FakeCompetencyRepository()
        competency = make_competency()
        competency_repository.save(competency)
        evaluation = make_evaluation(
            collaborator.id, evaluator.id, evaluation_repository
        )
        add_use_case = AddMeasurementToEvaluationUseCase(
            evaluation_repository, competency_repository
        )
        add_use_case.execute(
            evaluation.id,
            MeasurementCreateDTO(competency_id=competency.id.value, current_level=3),
        )
        submit_use_case = SubmitEvaluationUseCase(evaluation_repository)
        return submit_use_case, evaluation, evaluation_repository

    def test_should_submit_draft_with_measurements(self) -> None:
        """A draft with measurements is completed and frozen."""
        use_case, evaluation, repository = self._prepare()

        response = use_case.execute(evaluation.id)

        assert response.status.value == "COMPLETED"
        assert response.submitted_at is not None
        stored = repository.get_by_id(evaluation.id)
        assert stored is not None
        assert stored.status.value == "COMPLETED"

    def test_should_reject_submit_without_measurements(self) -> None:
        """Submitting requires at least one measurement."""
        evaluation_repository = FakeEvaluationRepository()
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        evaluator = make_collaborator()
        collaborator_repository.save(collaborator)
        collaborator_repository.save(evaluator)
        evaluation = make_evaluation(
            collaborator.id, evaluator.id, evaluation_repository
        )
        use_case = SubmitEvaluationUseCase(evaluation_repository)

        with pytest.raises(ValidationError, match="at least one measurement"):
            use_case.execute(evaluation.id)

    def test_should_reject_double_submit(self) -> None:
        """Submitting twice is not a valid transition."""
        use_case, evaluation, _ = self._prepare()
        use_case.execute(evaluation.id)

        with pytest.raises(ConflictError, match="transition"):
            use_case.execute(evaluation.id)


class TestAcceptEvaluationUseCase:
    """Test orchestration of AcceptEvaluationUseCase."""

    def _prepare(
        self,
    ) -> tuple[AcceptEvaluationUseCase, Evaluation, FakeEvaluationRepository]:
        """Create a submitted (COMPLETED) evaluation."""
        evaluation_repository = FakeEvaluationRepository()
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        evaluator = make_collaborator()
        collaborator_repository.save(collaborator)
        collaborator_repository.save(evaluator)
        competency_repository = FakeCompetencyRepository()
        competency = make_competency()
        competency_repository.save(competency)
        evaluation = make_evaluation(
            collaborator.id, evaluator.id, evaluation_repository
        )
        AddMeasurementToEvaluationUseCase(
            evaluation_repository, competency_repository
        ).execute(
            evaluation.id,
            MeasurementCreateDTO(competency_id=competency.id.value, current_level=3),
        )
        SubmitEvaluationUseCase(evaluation_repository).execute(evaluation.id)
        use_case = AcceptEvaluationUseCase(evaluation_repository)
        return use_case, evaluation, evaluation_repository

    def test_should_accept_completed_evaluation(self) -> None:
        """Accepting finalizes the evaluation as ACCEPTED."""
        use_case, evaluation, repository = self._prepare()

        response = use_case.execute(evaluation.id, response_notes="Agreed")

        assert response.status.value == "ACCEPTED"
        assert response.response_notes == "Agreed"
        assert response.response_date is not None
        stored = repository.get_by_id(evaluation.id)
        assert stored is not None
        assert stored.status.is_finalized()

    def test_should_reject_accepting_draft_evaluation(self) -> None:
        """Only completed evaluations can be accepted."""
        evaluation_repository = FakeEvaluationRepository()
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        evaluator = make_collaborator()
        collaborator_repository.save(collaborator)
        collaborator_repository.save(evaluator)
        evaluation = make_evaluation(
            collaborator.id, evaluator.id, evaluation_repository
        )
        use_case = AcceptEvaluationUseCase(evaluation_repository)

        with pytest.raises(ConflictError, match="transition"):
            use_case.execute(evaluation.id)


class TestContestEvaluationUseCase:
    """Test orchestration of ContestEvaluationUseCase."""

    def _prepare(
        self,
    ) -> tuple[ContestEvaluationUseCase, Evaluation, FakeEvaluationRepository]:
        """Create a submitted (COMPLETED) evaluation."""
        evaluation_repository = FakeEvaluationRepository()
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        evaluator = make_collaborator()
        collaborator_repository.save(collaborator)
        collaborator_repository.save(evaluator)
        competency_repository = FakeCompetencyRepository()
        competency = make_competency()
        competency_repository.save(competency)
        evaluation = make_evaluation(
            collaborator.id, evaluator.id, evaluation_repository
        )
        AddMeasurementToEvaluationUseCase(
            evaluation_repository, competency_repository
        ).execute(
            evaluation.id,
            MeasurementCreateDTO(competency_id=competency.id.value, current_level=3),
        )
        SubmitEvaluationUseCase(evaluation_repository).execute(evaluation.id)
        use_case = ContestEvaluationUseCase(evaluation_repository)
        return use_case, evaluation, evaluation_repository

    def test_should_contest_completed_evaluation_with_notes(self) -> None:
        """Contesting finalizes the evaluation as CONTESTED with notes."""
        use_case, evaluation, repository = self._prepare()

        response = use_case.execute(evaluation.id, response_notes="Level was too harsh")

        assert response.status.value == "CONTESTED"
        assert response.response_notes == "Level was too harsh"
        stored = repository.get_by_id(evaluation.id)
        assert stored is not None
        assert stored.status.is_finalized()

    def test_should_reject_contestation_without_notes(self) -> None:
        """Contestation notes are mandatory."""
        use_case, evaluation, _ = self._prepare()

        with pytest.raises(ValidationError, match=r"[Nn]otes"):
            use_case.execute(evaluation.id, response_notes="   ")

    def test_should_reject_contesting_draft_evaluation(self) -> None:
        """Only completed evaluations can be contested."""
        evaluation_repository = FakeEvaluationRepository()
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        evaluator = make_collaborator()
        collaborator_repository.save(collaborator)
        collaborator_repository.save(evaluator)
        evaluation = make_evaluation(
            collaborator.id, evaluator.id, evaluation_repository
        )
        use_case = ContestEvaluationUseCase(evaluation_repository)

        with pytest.raises(ConflictError, match="transition"):
            use_case.execute(evaluation.id, response_notes="Disagree")
