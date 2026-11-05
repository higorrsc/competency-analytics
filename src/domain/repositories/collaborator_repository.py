"""Repository abstraction for the collaborator aggregate."""

from typing import Protocol, runtime_checkable

from src.domain.entities.collaborator import Collaborator
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_id import PathId


@runtime_checkable
class CollaboratorRepository(Protocol):
    """
    Persistence contract for collaborators and their path enrollments.

    The domain defines this contract; infrastructure provides the concrete
    implementation. Implementations MUST persist the collaborator together
    with its enrollments, preserving inactive enrollments as history, and MUST
    NOT leak persistence models into the domain layer.
    """

    def save(self, collaborator: Collaborator) -> None:
        """
        Persist a collaborator, creating or updating it.

        Args:
            collaborator: Aggregate to persist.
        """
        ...

    def get_by_id(self, collaborator_id: CollaboratorId) -> Collaborator | None:
        """
        Retrieve a collaborator by identifier.

        Args:
            collaborator_id: Identifier of the collaborator.

        Returns:
            The collaborator when found, otherwise ``None``.
        """
        ...

    def find_by_path(
        self, path_id: PathId, *, active_only: bool = False
    ) -> list[Collaborator]:
        """
        Return collaborators enrolled in a career path.

        Args:
            path_id: Career path to filter by.
            active_only: When ``True``, only collaborators whose enrollment in
                the path is active are returned.

        Returns:
            Collaborators enrolled in the given path.
        """
        ...
