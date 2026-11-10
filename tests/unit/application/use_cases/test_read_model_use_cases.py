"""Unit tests for CQRS read model use cases."""

from __future__ import annotations

from datetime import UTC, datetime

from src.application.dto.read_model import (
    CompetencyHistoryEntryDTO,
    PathProgressionSummaryDTO,
)
from src.application.use_cases.read_model.query import (
    GetCompetencyHistoryUseCase,
    GetPathProgressionUseCase,
)
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.domain.value_objects.path_id import PathId


class FakeHistoryReadModel:
    """In-memory fake for CompetencyHistoryReadModel."""

    def __init__(self, entries: list[CompetencyHistoryEntryDTO]) -> None:
        self.entries = entries

    def get_history(
        self,
        collaborator_id: CollaboratorId,
        *,
        competency_id: CompetencyId | None = None,
        start_date: object = None,
        end_date: object = None,
    ) -> list[CompetencyHistoryEntryDTO]:
        result = [e for e in self.entries if e.collaborator_id == collaborator_id.value]
        if competency_id is not None:
            result = [e for e in result if e.competency_id == competency_id.value]
        return result


class FakeProgressionReadModel:
    """In-memory fake for PathProgressionReadModel."""

    def __init__(self, summary: PathProgressionSummaryDTO | None) -> None:
        self.summary = summary

    def get_progression_summary(
        self,
        collaborator_id: CollaboratorId,
        path_id: PathId,
    ) -> PathProgressionSummaryDTO | None:
        if (
            self.summary
            and self.summary.collaborator_id == collaborator_id.value
            and self.summary.path_id == path_id.value
        ):
            return self.summary
        return None


def test_get_competency_history_use_case() -> None:
    collab_id = CollaboratorId.generate()
    comp_id = CompetencyId.generate()
    entry = CompetencyHistoryEntryDTO(
        collaborator_id=collab_id.value,
        competency_id=comp_id.value,
        competency_name="Python",
        evaluation_date=datetime.now(UTC),
        period="2026.1",
        current_level=4,
        status=EvaluationStatus.ACCEPTED,
    )
    fake_model = FakeHistoryReadModel([entry])
    use_case = GetCompetencyHistoryUseCase(fake_model)

    results = use_case.execute(collab_id)
    assert len(results) == 1
    assert results[0].competency_name == "Python"

    filtered = use_case.execute(collab_id, competency_id=CompetencyId.generate())
    assert len(filtered) == 0


def test_get_path_progression_use_case() -> None:
    collab_id = CollaboratorId.generate()
    path_id = PathId.generate()
    summary = PathProgressionSummaryDTO(
        collaborator_id=collab_id.value,
        path_id=path_id.value,
        target_level="Senior",
        total_requirements=5,
        requirements_met=4,
        completion_percentage=80.0,
    )
    fake_model = FakeProgressionReadModel(summary)
    use_case = GetPathProgressionUseCase(fake_model)

    res = use_case.execute(collab_id, path_id)
    assert res is not None
    assert res.completion_percentage == 80.0

    none_res = use_case.execute(collab_id, PathId.generate())
    assert none_res is None
