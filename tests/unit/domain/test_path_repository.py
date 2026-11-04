"""Unit tests for the PathRepository protocol contract."""

from src.domain.entities.competency_path import CompetencyPath
from src.domain.repositories.path_repository import PathRepository
from src.domain.value_objects.path_id import PathId
from tests.unit.domain.test_competency_path import make_path


class FakePathRepository:
    """In-memory implementation used to validate the repository contract."""

    def __init__(self) -> None:
        """Initialize an empty in-memory path catalog."""
        self._paths: dict[PathId, CompetencyPath] = {}

    def save(self, path: CompetencyPath) -> None:
        """Store a path in memory."""
        self._paths[path.id] = path

    def get_by_id(self, path_id: PathId) -> CompetencyPath | None:
        """Return a stored path by identifier."""
        return self._paths.get(path_id)

    def find_all(self) -> list[CompetencyPath]:
        """Return every stored path."""
        return list(self._paths.values())


class TestPathRepositoryProtocol:
    """Test that the protocol describes the expected path contract."""

    def test_fake_repository_satisfies_protocol(self) -> None:
        """A structurally complete implementation is accepted."""
        repository: PathRepository = FakePathRepository()

        assert isinstance(repository, PathRepository)

    def test_save_and_get_by_id(self) -> None:
        """A saved path can be retrieved by identity."""
        repository = FakePathRepository()
        path = make_path()

        repository.save(path)

        assert repository.get_by_id(path.id) == path

    def test_get_by_id_returns_none_when_missing(self) -> None:
        """An unknown identifier yields no result."""
        repository = FakePathRepository()

        assert repository.get_by_id(PathId.generate()) is None

    def test_find_all_returns_every_path(self) -> None:
        """The full catalog is returned."""
        repository = FakePathRepository()
        first = make_path(name="Engineering")
        second = make_path(name="Management")
        repository.save(first)
        repository.save(second)

        assert set(repository.find_all()) == {first, second}

    def test_find_all_returns_empty_list_when_catalog_is_empty(self) -> None:
        """An empty catalog yields an empty list."""
        repository = FakePathRepository()

        assert repository.find_all() == []

    def test_save_updates_existing_path(self) -> None:
        """Saving the same identity replaces the stored aggregate."""
        repository = FakePathRepository()
        path = make_path(name="Engineering")
        repository.save(path)

        path.update_details(name="Software Engineering", description="Updated")
        repository.save(path)

        stored = repository.get_by_id(path.id)
        assert stored is not None
        assert stored.name == "Software Engineering"
        assert len(repository.find_all()) == 1
