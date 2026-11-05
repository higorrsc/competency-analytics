"""Shared in-memory repository fakes for application use case tests.

Fakes behave like real repositories (keyed upserts, real lookups) so use case
orchestration is exercised realistically without fresh mocks per test.
"""

from src.domain.entities.collaborator import Collaborator
from src.domain.entities.competency import Competency
from src.domain.entities.competency_path import CompetencyPath
from src.domain.entities.evaluation import Evaluation
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.evaluation_id import EvaluationId
from src.domain.value_objects.path_id import PathId


class FakeCompetencyRepository:
    """In-memory competency repository satisfying the domain protocol."""

    def __init__(self) -> None:
        """Initialize an empty in-memory catalog."""
        self._competencies: dict[CompetencyId, Competency] = {}

    def save(self, competency: Competency) -> None:
        """Store a competency, upserting by identifier."""
        self._competencies[competency.id] = competency

    def get_by_id(self, competency_id: CompetencyId) -> Competency | None:
        """Return a stored competency by identifier."""
        return self._competencies.get(competency_id)

    def find_by_hierarchy(
        self,
        *,
        category_id: object = None,
        group_id: object = None,
    ) -> list[Competency]:
        """Return competencies filtered by the provided hierarchy refs."""
        result = list(self._competencies.values())
        if category_id is not None:
            result = [c for c in result if c.category_id == category_id]
        if group_id is not None:
            result = [c for c in result if c.group_id == group_id]
        return result

    def delete(self, competency_id: CompetencyId) -> None:
        """Remove a competency from memory."""
        self._competencies.pop(competency_id, None)


class FakePathRepository:
    """In-memory career path repository satisfying the domain protocol."""

    def __init__(self) -> None:
        """Initialize an empty in-memory path store."""
        self._paths: dict[PathId, CompetencyPath] = {}

    def save(self, path: CompetencyPath) -> None:
        """Store a path, upserting by identifier."""
        self._paths[path.id] = path

    def get_by_id(self, path_id: PathId) -> CompetencyPath | None:
        """Return a stored path by identifier."""
        return self._paths.get(path_id)

    def find_all(self) -> list[CompetencyPath]:
        """Return every stored path."""
        return list(self._paths.values())


class FakeCollaboratorRepository:
    """In-memory collaborator repository satisfying the domain protocol."""

    def __init__(self) -> None:
        """Initialize an empty in-memory collaborator store."""
        self._collaborators: dict[CollaboratorId, Collaborator] = {}

    def save(self, collaborator: Collaborator) -> None:
        """Store a collaborator, upserting by identifier."""
        self._collaborators[collaborator.id] = collaborator

    def get_by_id(self, collaborator_id: CollaboratorId) -> Collaborator | None:
        """Return a stored collaborator by identifier."""
        return self._collaborators.get(collaborator_id)

    def find_by_path(
        self,
        path_id: PathId,
        *,
        active_only: bool = False,
    ) -> list[Collaborator]:
        """Return collaborators enrolled in the given path."""
        result = [
            collaborator
            for collaborator in self._collaborators.values()
            if (active_id := collaborator.active_enrollment()) is not None
            and active_id.path_id == path_id
        ]
        return result

    def find_all(self) -> list[Collaborator]:
        """Return all stored collaborators."""
        return list(self._collaborators.values())


class FakeEvaluationRepository:
    """In-memory evaluation repository satisfying the domain protocol."""

    def __init__(self) -> None:
        """Initialize an empty in-memory evaluation store."""
        self._evaluations: dict[EvaluationId, Evaluation] = {}

    def save(self, evaluation: Evaluation) -> None:
        """Store an evaluation, upserting by identifier."""
        self._evaluations[evaluation.id] = evaluation

    def get_by_id(self, evaluation_id: EvaluationId) -> Evaluation | None:
        """Return a stored evaluation by identifier."""
        return self._evaluations.get(evaluation_id)

    def find_latest_finalized_for_collaborator(
        self,
        collaborator_id: CollaboratorId,
    ) -> Evaluation | None:
        """Return the most recent finalized evaluation of a collaborator."""
        finalized = [
            evaluation
            for evaluation in self._evaluations.values()
            if evaluation.collaborator_id == collaborator_id
            and evaluation.status.is_finalized()
        ]
        if not finalized:
            return None
        return max(
            finalized,
            key=lambda evaluation: evaluation.evaluation_date,
        )

    def find_all(
        self, *, collaborator_id: CollaboratorId | None = None
    ) -> list[Evaluation]:
        """Return evaluations, optionally filtered by collaborator."""
        evals = list(self._evaluations.values())
        if collaborator_id is not None:
            evals = [e for e in evals if e.collaborator_id == collaborator_id]
        return sorted(evals, key=lambda e: e.evaluation_date, reverse=True)
