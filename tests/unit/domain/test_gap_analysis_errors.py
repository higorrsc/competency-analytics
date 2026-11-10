"""Unit tests for gap analysis domain exceptions."""

from src.domain.exceptions.domain_error import DomainError
from src.domain.exceptions.gap_analysis_errors import GapAnalysisError


class TestGapAnalysisError:
    """Test the gap analysis error."""

    def test_should_be_a_domain_error(self) -> None:
        """Gap analysis errors are domain errors."""
        error = GapAnalysisError("cannot calculate gaps")

        assert isinstance(error, DomainError)
        assert str(error) == "cannot calculate gaps"
