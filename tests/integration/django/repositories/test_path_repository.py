"""Integration tests for DjangoPathRepository."""

from __future__ import annotations

import pytest

from src.domain.entities.competency_path import CompetencyPath
from src.domain.entities.path_level import PathLevel
from src.domain.repositories.path_repository import PathRepository
from src.domain.value_objects.competency_requirement import CompetencyRequirement
from src.domain.value_objects.level_id import LevelId
from src.domain.value_objects.path_id import PathId
from src.domain.value_objects.requirement_weight import RequirementWeight
from src.infrastructure.django.repositories.competency_repository import (
    DjangoCompetencyRepository,
)
from src.infrastructure.django.repositories.path_repository import (
    DjangoPathRepository,
)
from tests.integration.django.repositories.helpers import make_competency


@pytest.mark.django_db
class TestDjangoPathRepository:
    """Tests for DjangoPathRepository implementing PathRepository."""

    def test_should_satisfy_protocol(self) -> None:
        """Repository satisfies the domain protocol."""
        repo = DjangoPathRepository()
        assert isinstance(repo, PathRepository)

    def test_should_save_and_retrieve_path_with_levels_and_requirements(
        self,
    ) -> None:
        """Career path with nested levels and requirements persists completely."""
        comp_repo = DjangoCompetencyRepository()
        comp = make_competency(name="Architecture")
        comp_repo.save(comp)

        repo = DjangoPathRepository()
        path = CompetencyPath(
            id=PathId.generate(),
            name="Software Engineering",
            description="Engineering career track",
            levels=[
                PathLevel(
                    id=LevelId.generate(),
                    name="Junior",
                    order=1,
                    requirements=[
                        CompetencyRequirement(
                            competency_id=comp.id,
                            minimum_level=2,
                            weight=RequirementWeight.CORE,
                        )
                    ],
                ),
                PathLevel(
                    id=LevelId.generate(),
                    name="Pleno",
                    order=2,
                    requirements=[
                        CompetencyRequirement(
                            competency_id=comp.id,
                            minimum_level=3,
                            weight=RequirementWeight.IMPORTANT,
                        )
                    ],
                ),
            ],
        )

        repo.save(path)
        loaded = repo.get_by_id(path.id)

        assert loaded is not None
        assert isinstance(loaded, CompetencyPath)
        assert loaded.id == path.id
        assert loaded.name == "Software Engineering"
        assert len(loaded.levels) == 2
        assert loaded.levels[0].name == "Junior"
        assert loaded.levels[0].order == 1
        assert len(loaded.levels[0].requirements) == 1
        assert loaded.levels[0].requirements[0].competency_id == comp.id
        assert loaded.levels[0].requirements[0].minimum_level == 2
        assert loaded.levels[0].requirements[0].weight == RequirementWeight.CORE

        assert loaded.levels[1].name == "Pleno"
        assert loaded.levels[1].requirements[0].minimum_level == 3
        assert loaded.levels[1].requirements[0].weight == RequirementWeight.IMPORTANT

    def test_should_update_path_levels_synchronization(self) -> None:
        """Saving a path synchronizes updated, added, and removed levels."""
        comp_repo = DjangoCompetencyRepository()
        comp = make_competency()
        comp_repo.save(comp)

        repo = DjangoPathRepository()
        path = CompetencyPath(
            id=PathId.generate(),
            name="Initial Path",
            description="Desc",
            levels=[
                PathLevel(
                    id=LevelId.generate(),
                    name="Level 1",
                    order=1,
                    requirements=[],
                )
            ],
        )
        repo.save(path)

        # Update path: add Level 2, rename Level 1
        path.levels[0].name = "Junior"
        path.levels.append(
            PathLevel(
                id=LevelId.generate(),
                name="Mid",
                order=2,
                requirements=[
                    CompetencyRequirement(
                        competency_id=comp.id,
                        minimum_level=3,
                        weight=RequirementWeight.DESIRABLE,
                    )
                ],
            )
        )
        repo.save(path)

        loaded = repo.get_by_id(path.id)
        assert loaded is not None
        assert len(loaded.levels) == 2
        assert loaded.levels[0].name == "Junior"
        assert loaded.levels[1].name == "Mid"
        assert len(loaded.levels[1].requirements) == 1

    def test_should_find_all_paths(self) -> None:
        """All paths are returned."""
        repo = DjangoPathRepository()
        p1 = CompetencyPath(id=PathId.generate(), name="Path A", description="D1")
        p2 = CompetencyPath(id=PathId.generate(), name="Path B", description="D2")
        repo.save(p1)
        repo.save(p2)

        all_paths = repo.find_all()
        assert len(all_paths) == 2
        assert [p.name for p in all_paths] == ["Path A", "Path B"]
