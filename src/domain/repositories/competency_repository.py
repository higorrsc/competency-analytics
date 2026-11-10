"""Repository abstraction for the competency catalog aggregate."""

from typing import Protocol, runtime_checkable

from src.domain.entities.competency import Competency
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.group_id import GroupId


@runtime_checkable
class CompetencyRepository(Protocol):
    """
    Persistence contract for the competency catalog.

    The domain defines this contract; infrastructure provides the concrete
    implementation (for example, a Django ORM repository). Implementations
    MUST translate between domain entities and their own persistence models
    and MUST NOT leak ORM models into the domain layer.

    Deletion is part of the contract because the catalog must refuse to
    remove a competency that is referenced by career paths or evaluations.
    Implementations raise ``CompetencyReferencedError`` in that case.
    """

    def save(self, competency: Competency) -> None:
        """
        Persist a competency, creating or updating it.

        Args:
            competency: Domain entity to persist.
        """
        ...

    def get_by_id(self, competency_id: CompetencyId) -> Competency | None:
        """
        Retrieve a competency by identifier.

        Args:
            competency_id: Identifier of the competency.

        Returns:
            The competency when found, otherwise ``None``.
        """
        ...

    def find_by_hierarchy(
        self,
        *,
        category_id: CategoryId | None = None,
        group_id: GroupId | None = None,
    ) -> list[Competency]:
        """
        List competencies filtered by their position in the hierarchy.

        Args:
            category_id: Optional category filter (top hierarchy level).
            group_id: Optional group filter (middle hierarchy level).

        Returns:
            Competencies matching every supplied filter. With no filters,
            every competency in the catalog is returned.
        """
        ...

    def delete(self, competency_id: CompetencyId) -> None:
        """
        Remove a competency from the catalog.

        Args:
            competency_id: Identifier of the competency to remove.

        Raises:
            CompetencyReferencedError: If the competency is still referenced
                by a career path or an evaluation measurement.
        """
        ...
