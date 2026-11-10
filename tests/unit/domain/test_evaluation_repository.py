"""Unit tests for the EvaluationRepository protocol contract."""

from datetime import UTC, datetime

from src.domain.entities.evaluation import Evaluation
from src.domain.repositories.evaluation_repository import EvaluationRepository
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.evaluation_id import EvaluationId
from src.domain.value_objects.evaluation_status import EvaluationStatus
from tests.unit.domain.test_evaluation import make_evaluation


class FakeEvaluationRepository:
    """In-memory implementation used to validate the repository contract."""

    def __init__(self) -> None:
        """Initialize an empty in-memory evaluation store."""
        self._evaluations: dict[EvaluationId, Evaluation] = {}

    def save(self, evaluation: Evaluation) -> None:
        """Store an evaluation in memory."""
        self._evaluations[evaluation.id] = evaluation

    def get_by_id(self, evaluation_id: EvaluationId) -> Evaluation | None:
        """Return a stored evaluation by identifier."""
        return self._evaluations.get(evaluation_id)

    def find_latest_finalized_for_collaborator(
        self, collaborator_id: CollaboratorId
    ) -> Evaluation | None:
        """Return the most recent finalized evaluation for a collaborator."""
        finalized = [
            evaluation
            for evaluation in self._evaluations.values()
            if evaluation.collaborator_id == collaborator_id
            and evaluation.status.is_finalized()
        ]
        if not finalized:
            return None
        return max(finalized, key=lambda evaluation: evaluation.evaluation_date)

    def find_all(
        self, *, collaborator_id: CollaboratorId | None = None
    ) -> list[Evaluation]:
        """Return all stored evaluations, optionally filtered."""
        evals = list(self._evaluations.values())
        if collaborator_id is not None:
            evals = [e for e in evals if e.collaborator_id == collaborator_id]
        return sorted(evals, key=lambda e: e.evaluation_date, reverse=True)


class TestEvaluationRepositoryProtocol:
    """Test that the protocol describes the expected evaluation contract."""

    def test_fake_repository_satisfies_protocol(self) -> None:
        """A structurally complete implementation is accepted."""
        repository: EvaluationRepository = FakeEvaluationRepository()

        assert isinstance(repository, EvaluationRepository)

    def test_save_and_get_by_id(self) -> None:
        """A saved evaluation can be retrieved by identity."""
        repository = FakeEvaluationRepository()
        evaluation = make_evaluation()

        repository.save(evaluation)

        assert repository.get_by_id(evaluation.id) == evaluation

    def test_get_by_id_returns_none_when_missing(self) -> None:
        """An unknown identifier yields no result."""
        repository = FakeEvaluationRepository()

        assert repository.get_by_id(EvaluationId.generate()) is None

    def test_find_latest_finalized_returns_none_without_history(self) -> None:
        """A collaborator without finalized evaluations yields no result."""
        repository = FakeEvaluationRepository()
        collaborator_id = CollaboratorId.generate()

        assert (
            repository.find_latest_finalized_for_collaborator(collaborator_id) is None
        )

    def test_find_latest_finalized_ignores_drafts_and_completed(self) -> None:
        """Only accepted or contested evaluations are considered finalized."""
        repository = FakeEvaluationRepository()
        collaborator_id = CollaboratorId.generate()
        repository.save(
            make_evaluation(
                collaborator_id=collaborator_id,
                status=EvaluationStatus.DRAFT,
            )
        )
        repository.save(
            make_evaluation(
                collaborator_id=collaborator_id,
                status=EvaluationStatus.COMPLETED,
            )
        )

        assert (
            repository.find_latest_finalized_for_collaborator(collaborator_id) is None
        )

    def test_find_latest_finalized_returns_most_recent(self) -> None:
        """The most recent finalized evaluation by date is returned."""
        repository = FakeEvaluationRepository()
        collaborator_id = CollaboratorId.generate()
        older = make_evaluation(
            collaborator_id=collaborator_id,
            evaluation_date=datetime(2025, 10, 1, tzinfo=UTC),
            status=EvaluationStatus.ACCEPTED,
        )
        newer = make_evaluation(
            collaborator_id=collaborator_id,
            evaluation_date=datetime(2026, 4, 1, tzinfo=UTC),
            status=EvaluationStatus.CONTESTED,
        )
        repository.save(newer)
        repository.save(older)

        assert (
            repository.find_latest_finalized_for_collaborator(collaborator_id) == newer
        )

    def test_find_latest_finalized_filters_by_collaborator(self) -> None:
        """Evaluations from other collaborators are ignored."""
        repository = FakeEvaluationRepository()
        collaborator_id = CollaboratorId.generate()
        expected = make_evaluation(
            collaborator_id=collaborator_id,
            status=EvaluationStatus.ACCEPTED,
        )
        repository.save(expected)
        repository.save(make_evaluation(status=EvaluationStatus.ACCEPTED))

        assert (
            repository.find_latest_finalized_for_collaborator(collaborator_id)
            == expected
        )

    def test_save_updates_existing_evaluation(self) -> None:
        """Saving the same identity replaces the stored aggregate."""
        repository = FakeEvaluationRepository()
        evaluation = make_evaluation(period="Q1 2026")
        repository.save(evaluation)

        evaluation.period = "Q2 2026"
        repository.save(evaluation)

        stored = repository.get_by_id(evaluation.id)
        assert stored is not None
        assert stored.period == "Q2 2026"
