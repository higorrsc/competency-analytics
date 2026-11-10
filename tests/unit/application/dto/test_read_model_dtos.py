"""Unit tests for read model DTOs."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.application.dto.read_model import (
    CompetencyHistoryEntryDTO,
    PathProgressionSummaryDTO,
)
from src.domain.value_objects.evaluation_status import EvaluationStatus

EVALUATION_DATE = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)


class TestCompetencyHistoryEntryDTO:
    """Test validation of CompetencyHistoryEntryDTO."""

    def test_should_accept_first_measurement(self) -> None:
        """First measurements carry no previous level or change."""
        dto = CompetencyHistoryEntryDTO(
            collaborator_id=uuid4(),
            competency_id=uuid4(),
            competency_name="Python",
            evaluation_date=EVALUATION_DATE,
            period="Q1 2026",
            current_level=3,
            previous_level=None,
            level_change=None,
            status="ACCEPTED",
        )

        assert dto.previous_level is None
        assert dto.level_change is None
        assert dto.status is EvaluationStatus.ACCEPTED

    def test_should_accept_repeat_measurement(self) -> None:
        """Repeat measurements carry previous level and change."""
        dto = CompetencyHistoryEntryDTO(
            collaborator_id=uuid4(),
            competency_id=uuid4(),
            competency_name="Python",
            evaluation_date=EVALUATION_DATE,
            period="Q1 2026",
            current_level=4,
            previous_level=2,
            level_change=2,
            status="CONTESTED",
        )

        assert dto.previous_level == 2
        assert dto.level_change == 2

    def test_should_reject_previous_level_without_change(self) -> None:
        """Previous level and change must be provided together."""
        with pytest.raises(
            ValidationError,
            match="previous_level and level_change must be provided together",
        ):
            CompetencyHistoryEntryDTO(
                collaborator_id=uuid4(),
                competency_id=uuid4(),
                competency_name="Python",
                evaluation_date=EVALUATION_DATE,
                period="Q1 2026",
                current_level=3,
                previous_level=2,
                status="ACCEPTED",
            )

    def test_should_reject_change_without_previous_level(self) -> None:
        """A change without previous level is inconsistent."""
        with pytest.raises(
            ValidationError,
            match="previous_level and level_change must be provided together",
        ):
            CompetencyHistoryEntryDTO(
                collaborator_id=uuid4(),
                competency_id=uuid4(),
                competency_name="Python",
                evaluation_date=EVALUATION_DATE,
                period="Q1 2026",
                current_level=3,
                level_change=2,
                status="ACCEPTED",
            )

    @pytest.mark.parametrize("level", [0, 6])
    def test_should_reject_current_level_outside_scale(self, level: int) -> None:
        """Current levels must be between 1 and 5."""
        with pytest.raises(ValidationError, match="current_level"):
            CompetencyHistoryEntryDTO(
                collaborator_id=uuid4(),
                competency_id=uuid4(),
                competency_name="Python",
                evaluation_date=EVALUATION_DATE,
                period="Q1 2026",
                current_level=level,
                status="ACCEPTED",
            )

    def test_should_reject_unknown_status(self) -> None:
        """Statuses must be supported lifecycle values."""
        with pytest.raises(ValidationError, match="status"):
            CompetencyHistoryEntryDTO(
                collaborator_id=uuid4(),
                competency_id=uuid4(),
                competency_name="Python",
                evaluation_date=EVALUATION_DATE,
                period="Q1 2026",
                current_level=3,
                status="CANCELLED",
            )


class TestPathProgressionSummaryDTO:
    """Test validation of PathProgressionSummaryDTO."""

    def test_should_accept_valid_summary(self) -> None:
        """A consistent progression summary is accepted."""
        dto = PathProgressionSummaryDTO(
            collaborator_id=uuid4(),
            path_id=uuid4(),
            target_level="Senior",
            total_requirements=10,
            requirements_met=7,
            completion_percentage=70.0,
        )

        assert dto.requirements_met == 7
        assert dto.completion_percentage == 70.0

    def test_should_reject_met_requirements_above_total(self) -> None:
        """Met requirements cannot exceed the total."""
        with pytest.raises(
            ValidationError,
            match="requirements_met cannot exceed total_requirements",
        ):
            PathProgressionSummaryDTO(
                collaborator_id=uuid4(),
                path_id=uuid4(),
                target_level="Senior",
                total_requirements=10,
                requirements_met=11,
                completion_percentage=100.0,
            )

    @pytest.mark.parametrize("total", [0, -1])
    def test_should_reject_non_positive_total(self, total: int) -> None:
        """A summary must reference at least one requirement."""
        with pytest.raises(ValidationError, match="total_requirements"):
            PathProgressionSummaryDTO(
                collaborator_id=uuid4(),
                path_id=uuid4(),
                target_level="Senior",
                total_requirements=total,
                requirements_met=0,
                completion_percentage=0.0,
            )

    @pytest.mark.parametrize("percentage", [-1.0, 101.0])
    def test_should_reject_percentage_outside_bounds(self, percentage: float) -> None:
        """Completion percentages must be between 0 and 100."""
        with pytest.raises(ValidationError, match="completion_percentage"):
            PathProgressionSummaryDTO(
                collaborator_id=uuid4(),
                path_id=uuid4(),
                target_level="Senior",
                total_requirements=10,
                requirements_met=5,
                completion_percentage=percentage,
            )
