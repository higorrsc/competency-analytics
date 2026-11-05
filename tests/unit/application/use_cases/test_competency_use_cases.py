"""Unit tests for the create competency use case."""

import pytest

from src.application.dto.competency_dtos import CompetencyCreateDTO
from src.application.use_cases.competency_use_cases import (
    CreateCompetencyUseCase,
)
from src.application.use_cases.errors import ValidationError
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
