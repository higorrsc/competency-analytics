"""Repository abstraction for the career path aggregate."""

from typing import Protocol, runtime_checkable

from src.domain.entities.competency_path import CompetencyPath
from src.domain.value_objects.path_id import PathId


@runtime_checkable
class PathRepository(Protocol):
    """
    Persistence contract for career paths.

    The domain defines this contract; infrastructure provides the concrete
    implementation. Implementations MUST map between the aggregate and their
    own persistence models without leaking them into the domain layer, and
    MUST persist levels and requirements together with their path.
    """

    def save(self, path: CompetencyPath) -> None:
        """
        Persist a career path, creating or updating it.

        Args:
            path: Aggregate to persist.
        """
        ...

    def get_by_id(self, path_id: PathId) -> CompetencyPath | None:
        """
        Retrieve a career path by identifier.

        Args:
            path_id: Identifier of the path.

        Returns:
            The path when found, otherwise ``None``.
        """
        ...

    def find_all(self) -> list[CompetencyPath]:
        """
        Return every career path.

        Returns:
            All paths in the catalog.
        """
        ...
