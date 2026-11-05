"""Unit tests for the read model protocol contracts."""

from datetime import UTC, date, datetime
from uuid import uuid4

from src.application.dto.read_model_dtos import (
    CompetencyHistoryEntryDTO,
    PathProgressionSummaryDTO,
)
from src.application.ports.read_models import (
    CompetencyHistoryReadModel,
    PathProgressionReadModel,
)
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.path_id import PathId

EVALUATION_DATE = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)


class FakeCompetencyHistoryReadModel:
    """In-memory implementation used to validate the history contract."""

    def __init__(self) -> None:
        """Initialize an empty in-memory history store."""
        self._entries: list[CompetencyHistoryEntryDTO] = []

    def add_entry(self, entry: CompetencyHistoryEntryDTO) -> None:
        """Store a history entry in memory."""
        self._entries.append(entry)

    def get_history(
        self,
        collaborator_id: CollaboratorId,
        *,
        competency_id: CompetencyId | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[CompetencyHistoryEntryDTO]:
        """Return stored entries filtered by the provided criteria."""
        result = [
            entry
            for entry in self._entries
            if entry.collaborator_id == collaborator_id.value
        ]
        if competency_id is not None:
            result = [
                entry for entry in result if entry.competency_id == competency_id.value
            ]
        return sorted(result, key=lambda entry: entry.evaluation_date)


class FakePathProgressionReadModel:
    """In-memory implementation used to validate the progression contract."""

    def __init__(self, summary: PathProgressionSummaryDTO | None = None) -> None:
        """
        Initialize the fake with an optional preloaded summary.

        Args:
            summary: Summary returned for every query.
        """
        self._summary = summary

    def get_progression_summary(
        self,
        collaborator_id: CollaboratorId,
        path_id: PathId,
    ) -> PathProgressionSummaryDTO | None:
        """Return the preloaded summary, if any."""
        return self._summary


def make_history_entry(
    competency_id: CompetencyId | None = None,
) -> CompetencyHistoryEntryDTO:
    """Build a valid history entry for use in tests."""
    return CompetencyHistoryEntryDTO(
        collaborator_id=uuid4(),
        competency_id=(competency_id or CompetencyId.generate()).value,
        competency_name="Python",
        evaluation_date=EVALUATION_DATE,
        period="Q1 2026",
        current_level=4,
        previous_level=3,
        level_change=1,
        status="ACCEPTED",
    )


def make_progression_summary() -> PathProgressionSummaryDTO:
    """Build a valid progression summary for use in tests."""
    return PathProgressionSummaryDTO(
        collaborator_id=uuid4(),
        path_id=uuid4(),
        target_level="Senior",
        total_requirements=10,
        requirements_met=7,
        completion_percentage=70.0,
    )


class TestCompetencyHistoryReadModelProtocol:
    """Test the history read model contract."""

    def test_fake_satisfies_protocol(self) -> None:
        """A structurally complete implementation is accepted."""
        read_model: CompetencyHistoryReadModel = FakeCompetencyHistoryReadModel()

        assert isinstance(read_model, CompetencyHistoryReadModel)

    def test_get_history_returns_stored_entries(self) -> None:
        """Stored entries can be queried."""
        read_model = FakeCompetencyHistoryReadModel()
        entry = make_history_entry()
        read_model.add_entry(entry)

        result = read_model.get_history(
            CollaboratorId(entry.collaborator_id),
        )

        assert result == [entry]

    def test_get_history_filters_by_competency(self) -> None:
        """Only entries for the requested competency are returned."""
        read_model = FakeCompetencyHistoryReadModel()
        python_id = CompetencyId.generate()
        python_entry = make_history_entry(competency_id=python_id)
        other_entry = make_history_entry()
        read_model.add_entry(python_entry)
        read_model.add_entry(other_entry)

        result = read_model.get_history(
            CollaboratorId(python_entry.collaborator_id),
            competency_id=python_id,
        )

        assert result == [python_entry]

    def test_get_history_returns_empty_without_entries(self) -> None:
        """An unknown collaborator yields no entries."""
        read_model = FakeCompetencyHistoryReadModel()

        assert read_model.get_history(CollaboratorId.generate()) == []


class TestPathProgressionReadModelProtocol:
    """Test the progression read model contract."""

    def test_fake_satisfies_protocol(self) -> None:
        """A structurally complete implementation is accepted."""
        read_model: PathProgressionReadModel = FakePathProgressionReadModel()

        assert isinstance(read_model, PathProgressionReadModel)

    def test_get_progression_summary_returns_summary(self) -> None:
        """A stored summary can be queried."""
        summary = make_progression_summary()
        read_model = FakePathProgressionReadModel(summary=summary)

        result = read_model.get_progression_summary(
            CollaboratorId(summary.collaborator_id),
            PathId(summary.path_id),
        )

        assert result == summary

    def test_get_progression_summary_returns_none(self) -> None:
        """A collaborator without progression data yields no summary."""
        read_model = FakePathProgressionReadModel()

        assert (
            read_model.get_progression_summary(
                CollaboratorId.generate(), PathId.generate()
            )
            is None
        )
