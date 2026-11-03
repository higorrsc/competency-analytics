"""Unit tests for ID value objects (EvaluationId, CompetencyId, PathId)."""

from uuid import UUID

import pytest

from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.evaluation_id import EvaluationId
from src.domain.value_objects.path_id import PathId


class TestEvaluationId:
    """Test EvaluationId value object."""

    def test_generate_creates_unique_ids(self) -> None:
        """Verify generate creates unique EvaluationId instances."""
        id1 = EvaluationId.generate()
        id2 = EvaluationId.generate()
        assert id1 != id2

    def test_from_string_valid_uuid(self) -> None:
        """Verify from_string creates EvaluationId from valid UUID string."""
        uuid_string = "123e4567-e89b-12d3-a456-426614174000"
        evaluation_id = EvaluationId.from_string(uuid_string)
        assert str(evaluation_id.value) == uuid_string

    def test_from_string_invalid_format_raises_error(self) -> None:
        """Verify from_string raises ValueError for invalid UUID format."""
        with pytest.raises(ValueError, match="Invalid EvaluationId format"):
            EvaluationId.from_string("not-a-uuid")

    def test_equality(self) -> None:
        """Verify two EvaluationIds with same UUID are equal."""
        uuid_value = UUID("123e4567-e89b-12d3-a456-426614174000")
        id1 = EvaluationId(uuid_value)
        id2 = EvaluationId(uuid_value)
        assert id1 == id2


class TestCompetencyId:
    """Test CompetencyId value object."""

    def test_generate_creates_unique_ids(self) -> None:
        """Verify generate creates unique CompetencyId instances."""
        id1 = CompetencyId.generate()
        id2 = CompetencyId.generate()
        assert id1 != id2

    def test_from_string_valid_uuid(self) -> None:
        """Verify from_string creates CompetencyId from valid UUID string."""
        uuid_string = "223e4567-e89b-12d3-a456-426614174000"
        competency_id = CompetencyId.from_string(uuid_string)
        assert str(competency_id.value) == uuid_string

    def test_from_string_invalid_format_raises_error(self) -> None:
        """Verify from_string raises ValueError for invalid UUID format."""
        with pytest.raises(ValueError, match="Invalid CompetencyId format"):
            CompetencyId.from_string("not-a-uuid")

    def test_equality(self) -> None:
        """Verify two CompetencyIds with same UUID are equal."""
        uuid_value = UUID("223e4567-e89b-12d3-a456-426614174000")
        id1 = CompetencyId(uuid_value)
        id2 = CompetencyId(uuid_value)
        assert id1 == id2


class TestPathId:
    """Test PathId value object."""

    def test_generate_creates_unique_ids(self) -> None:
        """Verify generate creates unique PathId instances."""
        id1 = PathId.generate()
        id2 = PathId.generate()
        assert id1 != id2

    def test_from_string_valid_uuid(self) -> None:
        """Verify from_string creates PathId from valid UUID string."""
        uuid_string = "323e4567-e89b-12d3-a456-426614174000"
        path_id = PathId.from_string(uuid_string)
        assert str(path_id.value) == uuid_string

    def test_from_string_invalid_format_raises_error(self) -> None:
        """Verify from_string raises ValueError for invalid UUID format."""
        with pytest.raises(ValueError, match="Invalid PathId format"):
            PathId.from_string("not-a-uuid")

    def test_equality(self) -> None:
        """Verify two PathIds with same UUID are equal."""
        uuid_value = UUID("323e4567-e89b-12d3-a456-426614174000")
        id1 = PathId(uuid_value)
        id2 = PathId(uuid_value)
        assert id1 == id2
