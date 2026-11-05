"""Unit tests for the CollaboratorRepository protocol contract."""

from src.domain.entities.collaborator import Collaborator
from src.domain.repositories.collaborator_repository import CollaboratorRepository
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_id import PathId
from tests.unit.domain.test_collaborator import (
    make_collaborator,
    make_enrollment,
)


class FakeCollaboratorRepository:
    """In-memory implementation used to validate the repository contract."""

    def __init__(self) -> None:
        """Initialize an empty in-memory collaborator store."""
        self._collaborators: dict[CollaboratorId, Collaborator] = {}

    def save(self, collaborator: Collaborator) -> None:
        """Store a collaborator in memory."""
        self._collaborators[collaborator.id] = collaborator

    def get_by_id(self, collaborator_id: CollaboratorId) -> Collaborator | None:
        """Return a stored collaborator by identifier."""
        return self._collaborators.get(collaborator_id)

    def find_by_path(
        self, path_id: PathId, *, active_only: bool = False
    ) -> list[Collaborator]:
        """Return collaborators enrolled in a path, optionally active only."""
        result: list[Collaborator] = []
        for collaborator in self._collaborators.values():
            enrollment = collaborator.find_enrollment(path_id)
            if enrollment is None:
                continue
            if active_only and not enrollment.is_active:
                continue
            result.append(collaborator)
        return result

    def find_all(self) -> list[Collaborator]:
        """Return all stored collaborators."""
        return list(self._collaborators.values())


class TestCollaboratorRepositoryProtocol:
    """Test that the protocol describes the expected collaborator contract."""

    def test_fake_repository_satisfies_protocol(self) -> None:
        """A structurally complete implementation is accepted."""
        repository: CollaboratorRepository = FakeCollaboratorRepository()

        assert isinstance(repository, CollaboratorRepository)

    def test_save_and_get_by_id(self) -> None:
        """A saved collaborator can be retrieved by identity."""
        repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()

        repository.save(collaborator)

        assert repository.get_by_id(collaborator.id) == collaborator

    def test_get_by_id_returns_none_when_missing(self) -> None:
        """An unknown identifier yields no result."""
        repository = FakeCollaboratorRepository()

        assert repository.get_by_id(CollaboratorId.generate()) is None

    def test_find_by_path_returns_enrolled_collaborators(self) -> None:
        """Only collaborators enrolled in the path are returned."""
        repository = FakeCollaboratorRepository()
        path_id = PathId.generate()
        enrolled = make_collaborator(enrollments=[make_enrollment(path_id=path_id)])
        other = make_collaborator()
        repository.save(enrolled)
        repository.save(other)

        assert repository.find_by_path(path_id) == [enrolled]

    def test_find_by_path_returns_empty_when_nobody_is_enrolled(self) -> None:
        """An unused path yields an empty list."""
        repository = FakeCollaboratorRepository()
        repository.save(make_collaborator())

        assert repository.find_by_path(PathId.generate()) == []

    def test_find_by_path_filters_active_enrollments(self) -> None:
        """Active-only queries exclude inactive enrollments."""
        repository = FakeCollaboratorRepository()
        path_id = PathId.generate()
        inactive = make_collaborator(
            enrollments=[make_enrollment(path_id=path_id, is_active=False)]
        )
        active = make_collaborator(
            enrollments=[make_enrollment(path_id=path_id, is_active=True)]
        )
        repository.save(inactive)
        repository.save(active)

        assert set(repository.find_by_path(path_id)) == {inactive, active}
        assert repository.find_by_path(path_id, active_only=True) == [active]

    def test_save_updates_existing_collaborator(self) -> None:
        """Saving the same identity replaces the stored aggregate."""
        repository = FakeCollaboratorRepository()
        collaborator = make_collaborator(department="Engineering")
        repository.save(collaborator)

        collaborator.department = "Platform"
        repository.save(collaborator)

        stored = repository.get_by_id(collaborator.id)
        assert stored is not None
        assert stored.department == "Platform"
        assert len(repository.find_by_path(PathId.generate())) == 0
