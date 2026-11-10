"""Unit tests for the CompetencyRepository protocol contract."""

from src.domain.entities.competency import Competency
from src.domain.repositories.competency_repository import CompetencyRepository
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.group_id import GroupId
from tests.unit.domain.test_competency import make_competency


class FakeCompetencyRepository:
    """In-memory implementation used to validate the repository contract."""

    def __init__(self) -> None:
        """Initialize an empty in-memory catalog."""
        self._competencies: dict[CompetencyId, Competency] = {}

    def save(self, competency: Competency) -> None:
        """Store a competency in memory."""
        self._competencies[competency.id] = competency

    def get_by_id(self, competency_id: CompetencyId) -> Competency | None:
        """Return a stored competency by identifier."""
        return self._competencies.get(competency_id)

    def find_by_hierarchy(
        self,
        *,
        category_id: CategoryId | None = None,
        group_id: GroupId | None = None,
    ) -> list[Competency]:
        """Return competencies matching every supplied hierarchy filter."""
        results: list[Competency] = []
        for competency in self._competencies.values():
            if category_id is not None and competency.category_id != category_id:
                continue
            if group_id is not None and competency.group_id != group_id:
                continue
            results.append(competency)
        return results

    def delete(self, competency_id: CompetencyId) -> None:
        """Remove a competency from memory."""
        self._competencies.pop(competency_id, None)


class TestCompetencyRepositoryProtocol:
    """Test that the protocol describes the expected catalog contract."""

    def test_fake_repository_satisfies_protocol(self) -> None:
        """A structurally complete implementation is accepted."""
        repository: CompetencyRepository = FakeCompetencyRepository()

        assert isinstance(repository, CompetencyRepository)

    def test_save_and_get_by_id(self) -> None:
        """A saved competency can be retrieved by identity."""
        repository = FakeCompetencyRepository()
        competency = make_competency()

        repository.save(competency)

        assert repository.get_by_id(competency.id) == competency

    def test_get_by_id_returns_none_when_missing(self) -> None:
        """An unknown identifier yields no result."""
        repository = FakeCompetencyRepository()

        assert repository.get_by_id(CompetencyId.generate()) is None

    def test_find_by_hierarchy_without_filters_returns_all(self) -> None:
        """No filters means the whole catalog."""
        repository = FakeCompetencyRepository()
        first = make_competency()
        second = make_competency()
        repository.save(first)
        repository.save(second)

        assert set(repository.find_by_hierarchy()) == {first, second}

    def test_find_by_hierarchy_filters_by_category(self) -> None:
        """The category filter narrows the result set."""
        repository = FakeCompetencyRepository()
        category_id = CategoryId.generate()
        matching = make_competency(category_id=category_id)
        other = make_competency()
        repository.save(matching)
        repository.save(other)

        assert repository.find_by_hierarchy(category_id=category_id) == [matching]

    def test_find_by_hierarchy_filters_by_group(self) -> None:
        """The group filter narrows the result set."""
        repository = FakeCompetencyRepository()
        group_id = GroupId.generate()
        matching = make_competency(group_id=group_id)
        other = make_competency()
        repository.save(matching)
        repository.save(other)

        assert repository.find_by_hierarchy(group_id=group_id) == [matching]

    def test_find_by_hierarchy_combines_filters(self) -> None:
        """Category and group filters are applied together."""
        repository = FakeCompetencyRepository()
        category_id = CategoryId.generate()
        group_id = GroupId.generate()
        matching = make_competency(category_id=category_id, group_id=group_id)
        repository.save(matching)
        repository.save(make_competency(category_id=category_id))
        repository.save(make_competency(group_id=group_id))

        result = repository.find_by_hierarchy(
            category_id=category_id,
            group_id=group_id,
        )

        assert result == [matching]

    def test_delete_removes_competency(self) -> None:
        """A deleted competency is no longer retrievable."""
        repository = FakeCompetencyRepository()
        competency = make_competency()
        repository.save(competency)

        repository.delete(competency.id)

        assert repository.get_by_id(competency.id) is None
