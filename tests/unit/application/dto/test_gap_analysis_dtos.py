"""Unit tests for gap analysis DTOs."""

from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.application.dto.gap_analysis import (
    CompetencyGapDTO,
    GapAnalysisRequestDTO,
    GapAnalysisResponseDTO,
    ProgressionEligibilityDTO,
)


class TestGapAnalysisRequestDTO:
    """Test validation of GapAnalysisRequestDTO."""

    def test_should_accept_valid_request(self) -> None:
        """A request with all references is accepted."""
        dto = GapAnalysisRequestDTO(
            collaborator_id=uuid4(),
            path_id=uuid4(),
            level_id=uuid4(),
        )

        assert isinstance(dto.collaborator_id, UUID)
        assert isinstance(dto.path_id, UUID)
        assert isinstance(dto.level_id, UUID)

    def test_should_reject_malformed_references(self) -> None:
        """References must be valid UUIDs."""
        with pytest.raises(ValidationError, match="level_id"):
            GapAnalysisRequestDTO(
                collaborator_id=uuid4(),
                path_id=uuid4(),
                level_id="not-a-uuid",
            )


class TestCompetencyGapDTO:
    """Test validation of CompetencyGapDTO."""

    def test_should_accept_valid_gap(self) -> None:
        """A gap with consistent data is accepted."""
        competency_id = uuid4()

        dto = CompetencyGapDTO(
            competency_id=competency_id,
            current_level=2,
            required_level=4,
            gap=2,
            weight="CORE",
        )

        assert dto.competency_id == competency_id
        assert dto.weight.value == "CORE"

    def test_should_accept_unmeasured_gap(self) -> None:
        """Level 0 represents unmeasured competencies."""
        dto = CompetencyGapDTO(
            competency_id=uuid4(),
            current_level=0,
            required_level=4,
            gap=4,
            weight="IMPORTANT",
        )

        assert dto.current_level == 0

    @pytest.mark.parametrize("current_level", [-1, 6])
    def test_should_reject_current_level_outside_range(
        self, current_level: int
    ) -> None:
        """Current levels must be 0 or between 1 and 5."""
        with pytest.raises(ValidationError, match="current_level"):
            CompetencyGapDTO(
                competency_id=uuid4(),
                current_level=current_level,
                required_level=4,
                gap=2,
                weight="CORE",
            )

    @pytest.mark.parametrize("required_level", [0, 6])
    def test_should_reject_required_level_outside_scale(
        self, required_level: int
    ) -> None:
        """Required levels must be between 1 and 5."""
        with pytest.raises(ValidationError, match="required_level"):
            CompetencyGapDTO(
                competency_id=uuid4(),
                current_level=2,
                required_level=required_level,
                gap=2,
                weight="CORE",
            )

    def test_should_reject_negative_gap(self) -> None:
        """Gap sizes cannot be negative."""
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            CompetencyGapDTO(
                competency_id=uuid4(),
                current_level=2,
                required_level=4,
                gap=int("-1"),
                weight="CORE",
            )


class TestProgressionEligibilityDTO:
    """Test validation of ProgressionEligibilityDTO."""

    def test_should_accept_eligible_result(self) -> None:
        """An eligible result may have no blockers."""
        dto = ProgressionEligibilityDTO(is_eligible=True)

        assert dto.is_eligible is True
        assert dto.blocking_competency_ids == []

    def test_should_accept_ineligible_result_with_blockers(self) -> None:
        """An ineligible result lists blocking competencies."""
        blocker = uuid4()

        dto = ProgressionEligibilityDTO(
            is_eligible=False,
            blocking_competency_ids=[blocker],
        )

        assert dto.blocking_competency_ids == [blocker]

    def test_should_reject_invalid_boolean(self) -> None:
        """The eligibility flag must be a boolean."""
        with pytest.raises(ValidationError, match="is_eligible"):
            ProgressionEligibilityDTO(is_eligible=42)  # type: ignore[arg-type]


class TestGapAnalysisResponseDTO:
    """Test mapping of GapAnalysisResponseDTO."""

    def test_should_accept_valid_response(self) -> None:
        """A response with gaps and eligibility is accepted."""
        blocker = uuid4()
        eligibility = ProgressionEligibilityDTO(
            is_eligible=False,
            blocking_competency_ids=[blocker],
        )

        dto = GapAnalysisResponseDTO(
            gaps=[
                CompetencyGapDTO(
                    competency_id=uuid4(),
                    current_level=2,
                    required_level=4,
                    gap=2,
                    weight="CORE",
                )
            ],
            eligibility=eligibility,
        )

        assert len(dto.gaps) == 1
        assert dto.eligibility.blocking_competency_ids == [blocker]

    def test_should_accept_empty_response(self) -> None:
        """A path level without requirements produces an empty response."""
        dto = GapAnalysisResponseDTO(
            gaps=[],
            eligibility=ProgressionEligibilityDTO(is_eligible=True),
        )

        assert dto.gaps == []
