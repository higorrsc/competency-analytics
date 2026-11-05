"""Unit tests for the create competency use case."""

import pytest

from src.application.dto.competency_dtos import CompetencyCreateDTO
from src.application.use_cases.competency_use_cases import (
    CreateCompetencyUseCase,
    DeleteCompetencyUseCase,
    GetCompetencyUseCase,
    ListCompetenciesUseCase,
)
from src.application.use_cases.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.domain.exceptions.competency_errors import CompetencyReferencedError
from src.domain.repositories.competency_repository import CompetencyRepository
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.group_id import GroupId
from tests.unit.application.use_cases.fakes import FakeCompetencyRepository

LEVEL_DESCRIPTIONS = {
    1: "None",
    2: "Basic",
    3: "Good",
    4: "Strong",
    5: "Expert",
}

CATEGORY_ID = CategoryId.generate()
GROUP_ID = GroupId.generate()


def make_dto() -> CompetencyCreateDTO:
    """Build a valid competency creation DTO."""
    return CompetencyCreateDTO(
        name="Python",
        description="Programming language",
        category_id=CATEGORY_ID.value,
        group_id=GROUP_ID.value,
        level_descriptions=LEVEL_DESCRIPTIONS,
    )


class TestCreateCompetencyUseCase:
    """Test orchestration of CreateCompetencyUseCase."""

    def test_should_create_competency_when_input_is_valid(self) -> None:
        """A valid DTO results in a persisted competency."""
        repository = FakeCompetencyRepository()
        use_case = CreateCompetencyUseCase(repository)

        response = use_case.execute(make_dto())

        assert response.name == "Python"
        assert response.category_id == CATEGORY_ID.value
        assert response.group_id == GROUP_ID.value
        assert repository.get_by_id(CompetencyId(response.id)) is not None

    def test_should_return_response_dto_with_stored_data(self) -> None:
        """The response reflects exactly the stored entity."""
        repository = FakeCompetencyRepository()
        use_case = CreateCompetencyUseCase(repository)

        response = use_case.execute(make_dto())

        assert response.level_descriptions == LEVEL_DESCRIPTIONS

    def test_should_reject_competency_with_blank_name(self) -> None:
        """Blank names fail after domain validation."""
        use_case = CreateCompetencyUseCase(FakeCompetencyRepository())
        dto = CompetencyCreateDTO.model_construct(
            name="   ",
            description="Programming language",
            category_id=CATEGORY_ID.value,
            group_id=GROUP_ID.value,
            level_descriptions=LEVEL_DESCRIPTIONS,
        )

        with pytest.raises(ValidationError, match="name must not be empty"):
            use_case.execute(dto)

    def test_should_reject_competency_with_incomplete_levels(self) -> None:
        """A missing level description is rejected."""
        use_case = CreateCompetencyUseCase(FakeCompetencyRepository())
        dto = CompetencyCreateDTO.model_construct(
            name="Python",
            description="Programming language",
            category_id=CATEGORY_ID.value,
            group_id=GROUP_ID.value,
            level_descriptions={k: v for k, v in LEVEL_DESCRIPTIONS.items() if k != 5},
        )

        with pytest.raises(
            ValidationError,
            match="Missing descriptions",
        ):
            use_case.execute(dto)


class TestCompetencyRepositoryProtocolConformance:
    """Sanity check that the fake satisfies the domain protocol."""

    def test_fake_satisfies_protocol(self) -> None:
        """The fake structurally satisfies the repository protocol."""
        assert isinstance(FakeCompetencyRepository(), CompetencyRepository)


class TestGetCompetencyUseCase:
    """Tests for GetCompetencyUseCase."""

    def test_should_return_competency_when_found(self) -> None:
        repository = FakeCompetencyRepository()
        created = CreateCompetencyUseCase(repository).execute(make_dto())

        use_case = GetCompetencyUseCase(repository)
        response = use_case.execute(CompetencyId(created.id))

        assert response.id == created.id
        assert response.name == "Python"

    def test_should_raise_not_found_when_competency_does_not_exist(self) -> None:
        use_case = GetCompetencyUseCase(FakeCompetencyRepository())
        with pytest.raises(NotFoundError):
            use_case.execute(CompetencyId.generate())


class TestListCompetenciesUseCase:
    """Tests for ListCompetenciesUseCase."""

    def test_should_list_all_competencies(self) -> None:
        repository = FakeCompetencyRepository()
        create = CreateCompetencyUseCase(repository)
        c1 = create.execute(make_dto())
        c2 = create.execute(
            CompetencyCreateDTO(
                name="Java",
                description="Backend",
                category_id=CATEGORY_ID.value,
                group_id=GROUP_ID.value,
                level_descriptions=LEVEL_DESCRIPTIONS,
            )
        )

        use_case = ListCompetenciesUseCase(repository)
        results = use_case.execute()

        assert len(results) == 2
        ids = {r.id for r in results}
        assert c1.id in ids
        assert c2.id in ids

    def test_should_filter_by_category_and_group(self) -> None:
        repository = FakeCompetencyRepository()
        create = CreateCompetencyUseCase(repository)
        other_group = GroupId.generate()
        create.execute(make_dto())
        c2 = create.execute(
            CompetencyCreateDTO(
                name="Java",
                description="Backend",
                category_id=CATEGORY_ID.value,
                group_id=other_group.value,
                level_descriptions=LEVEL_DESCRIPTIONS,
            )
        )

        use_case = ListCompetenciesUseCase(repository)
        results = use_case.execute(group_id=other_group)
        assert len(results) == 1
        assert results[0].id == c2.id


class TestDeleteCompetencyUseCase:
    """Tests for DeleteCompetencyUseCase."""

    def test_should_delete_unreferenced_competency(self) -> None:
        repository = FakeCompetencyRepository()
        created = CreateCompetencyUseCase(repository).execute(make_dto())

        use_case = DeleteCompetencyUseCase(repository)
        use_case.execute(CompetencyId(created.id))

        assert repository.get_by_id(CompetencyId(created.id)) is None

    def test_should_raise_not_found_when_competency_absent(self) -> None:
        use_case = DeleteCompetencyUseCase(FakeCompetencyRepository())
        with pytest.raises(NotFoundError):
            use_case.execute(CompetencyId.generate())

    def test_should_raise_conflict_when_competency_referenced(self) -> None:
        repository = FakeCompetencyRepository()
        created = CreateCompetencyUseCase(repository).execute(make_dto())

        def mock_delete(cid: CompetencyId) -> None:
            raise CompetencyReferencedError(cid)

        repository.delete = mock_delete  # type: ignore[method-assign]
        use_case = DeleteCompetencyUseCase(repository)

        with pytest.raises(ConflictError):
            use_case.execute(CompetencyId(created.id))
