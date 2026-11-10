"""Unit tests for career path domain exceptions."""

from src.domain.exceptions.domain_error import DomainError
from src.domain.exceptions.path_errors import (
    CompetencyPathValidationError,
    LevelNotFoundError,
)
from src.domain.value_objects.level_id import LevelId


class TestCompetencyPathValidationError:
    """Test the career path validation error."""

    def test_should_be_a_domain_error(self) -> None:
        """Validation errors are domain errors."""
        error = CompetencyPathValidationError("invalid path")

        assert isinstance(error, DomainError)
        assert str(error) == "invalid path"


class TestLevelNotFoundError:
    """Test the missing-level error."""

    def test_should_be_a_domain_error(self) -> None:
        """Missing-level errors are domain errors."""
        error = LevelNotFoundError(LevelId.generate())

        assert isinstance(error, DomainError)

    def test_should_expose_level_id(self) -> None:
        """The error keeps the identifier for callers to inspect."""
        level_id = LevelId.generate()

        error = LevelNotFoundError(level_id)

        assert error.level_id == level_id

    def test_should_build_descriptive_message(self) -> None:
        """The message names the missing level."""
        level_id = LevelId.generate()

        error = LevelNotFoundError(level_id)

        assert str(level_id) in str(error)
        assert "was not found" in str(error)
