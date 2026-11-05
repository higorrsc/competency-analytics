"""Unit tests for the create career path use case."""

import pytest

from src.application.dto.path_dtos import (
    LevelCreateDTO,
    PathCreateDTO,
    RequirementCreateDTO,
)
from src.application.use_cases.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.application.use_cases.path_use_cases import (
    CreateCareerPathUseCase,
    GetCareerPathUseCase,
    ListCareerPathsUseCase,
)
from src.domain.entities.competency import Competency
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.group_id import GroupId
from src.domain.value_objects.path_id import PathId
from src.domain.value_objects.requirement_weight import RequirementWeight
from tests.unit.application.use_cases.fakes import (
    FakeCompetencyRepository,
    FakePathRepository,
)

LEVEL_DESCRIPTIONS = {
    1: "None",
    2: "Basic",
    3: "Good",
    4: "Strong",
    5: "Expert",
}


def make_competency() -> Competency:
    """Build a valid stored competency for requirement resolution."""
    return Competency(
        id=CompetencyId.generate(),
        name="Python",
        description="Programming language",
        category_id=CategoryId.generate(),
        group_id=GroupId.generate(),
        level_descriptions=LEVEL_DESCRIPTIONS,
    )


def make_requirement(
    competency_id: CompetencyId | None = None,
    minimum_level: int = 4,
    weight: RequirementWeight = RequirementWeight.CORE,
) -> RequirementCreateDTO:
    """Build a valid requirement DTO for an existing competency."""
    if competency_id is None:
        competency_id = CompetencyId.generate()
    return RequirementCreateDTO(
        competency_id=competency_id.value,
        minimum_level=minimum_level,
        weight=weight,
    )


class TestCreateCareerPathUseCase:
    """Test orchestration of CreateCareerPathUseCase."""

    def test_should_create_path_without_levels(self) -> None:
        """A path may be created with no levels defined yet."""
        path_repository = FakePathRepository()
        use_case = CreateCareerPathUseCase(path_repository, FakeCompetencyRepository())

        response = use_case.execute(
            PathCreateDTO(name="Software Engineer Track", description="Progression")
        )

        assert response.name == "Software Engineer Track"
        assert response.levels == []
        assert path_repository.get_by_id(PathId(response.id)) is not None

    def test_should_create_path_with_ordered_levels_and_requirements(self) -> None:
        """Levels are stored ordered and requirements resolve competencies."""
        competency_repository = FakeCompetencyRepository()
        competency = make_competency()
        competency_repository.save(competency)
        path_repository = FakePathRepository()
        use_case = CreateCareerPathUseCase(path_repository, competency_repository)

        response = use_case.execute(
            PathCreateDTO(
                name="Software Engineer Track",
                description="Engineering progression",
                levels=[
                    LevelCreateDTO(
                        name="Junior",
                        order=1,
                        requirements=[
                            make_requirement(competency.id, 2, RequirementWeight.CORE)
                        ],
                    ),
                    LevelCreateDTO(name="Senior", order=2),
                ],
            )
        )

        assert [level.name for level in response.levels] == ["Junior", "Senior"]
        assert response.levels[0].requirements[0].competency_id == competency.id.value
        stored = path_repository.get_by_id(PathId(response.id))
        assert stored is not None
        assert stored.levels[0].requirements[0].minimum_level == 2

    def test_should_reject_requirement_for_unknown_competency(self) -> None:
        """Requirements must reference competencies that exist."""
        use_case = CreateCareerPathUseCase(
            FakePathRepository(), FakeCompetencyRepository()
        )

        with pytest.raises(NotFoundError, match="Competency"):
            use_case.execute(
                PathCreateDTO(
                    name="Track",
                    description="Description",
                    levels=[
                        LevelCreateDTO(
                            name="Junior",
                            order=1,
                            requirements=[make_requirement()],
                        )
                    ],
                )
            )

    @pytest.mark.parametrize("orders", [[1, 3], [1, 1], [2]])
    def test_should_reject_non_contiguous_level_orders(self, orders: list[int]) -> None:
        """Level orders must be a contiguous 1..N sequence."""
        use_case = CreateCareerPathUseCase(
            FakePathRepository(), FakeCompetencyRepository()
        )

        with pytest.raises(ValidationError, match="contiguous orders"):
            use_case.execute(
                PathCreateDTO(
                    name="Track",
                    description="Description",
                    levels=[LevelCreateDTO(name=f"Level {n}", order=n) for n in orders],
                )
            )

    def test_should_reject_duplicate_level_names(self) -> None:
        """The domain rejects duplicated level names."""
        use_case = CreateCareerPathUseCase(
            FakePathRepository(), FakeCompetencyRepository()
        )

        with pytest.raises(ConflictError, match=r"[Dd]uplicate"):
            use_case.execute(
                PathCreateDTO(
                    name="Track",
                    description="Description",
                    levels=[
                        LevelCreateDTO(name="Junior", order=1),
                        LevelCreateDTO(name="junior", order=2),
                    ],
                )
            )


class TestGetCareerPathUseCase:
    """Tests for GetCareerPathUseCase."""

    def test_should_return_path_when_found(self) -> None:
        path_repo = FakePathRepository()
        comp_repo = FakeCompetencyRepository()
        created = CreateCareerPathUseCase(path_repo, comp_repo).execute(
            PathCreateDTO(
                name="Backend Track",
                description="Path for backend devs",
                levels=[LevelCreateDTO(name="Junior", order=1)],
            )
        )

        use_case = GetCareerPathUseCase(path_repo)
        response = use_case.execute(PathId(created.id))

        assert response.id == created.id
        assert response.name == "Backend Track"
        assert len(response.levels) == 1

    def test_should_raise_not_found_when_path_absent(self) -> None:
        use_case = GetCareerPathUseCase(FakePathRepository())
        with pytest.raises(NotFoundError):
            use_case.execute(PathId.generate())


class TestListCareerPathsUseCase:
    """Tests for ListCareerPathsUseCase."""

    def test_should_return_all_paths(self) -> None:
        path_repo = FakePathRepository()
        comp_repo = FakeCompetencyRepository()
        create = CreateCareerPathUseCase(path_repo, comp_repo)

        p1 = create.execute(
            PathCreateDTO(
                name="Track 1",
                description="Desc 1",
                levels=[LevelCreateDTO(name="L1", order=1)],
            )
        )
        p2 = create.execute(
            PathCreateDTO(
                name="Track 2",
                description="Desc 2",
                levels=[LevelCreateDTO(name="L1", order=1)],
            )
        )

        use_case = ListCareerPathsUseCase(path_repo)
        results = use_case.execute()

        assert len(results) == 2
        ids = {r.id for r in results}
        assert p1.id in ids
        assert p2.id in ids
