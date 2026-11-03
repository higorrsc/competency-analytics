"""Unit tests for EvaluationStatus enum."""

import pytest

from src.domain.value_objects.evaluation_status import EvaluationStatus


class TestEvaluationStatus:
    """Test EvaluationStatus enum and its state transition methods."""

    def test_all_states_defined(self) -> None:
        """Verify all four states are defined."""
        assert EvaluationStatus.DRAFT.value == "DRAFT"
        assert EvaluationStatus.COMPLETED.value == "COMPLETED"
        assert EvaluationStatus.ACCEPTED.value == "ACCEPTED"
        assert EvaluationStatus.CONTESTED.value == "CONTESTED"

    def test_is_draft(self) -> None:
        """Verify is_draft returns True only for DRAFT."""
        assert EvaluationStatus.DRAFT.is_draft() is True
        assert EvaluationStatus.COMPLETED.is_draft() is False
        assert EvaluationStatus.ACCEPTED.is_draft() is False
        assert EvaluationStatus.CONTESTED.is_draft() is False

    def test_is_finalized(self) -> None:
        """Verify is_finalized returns True for ACCEPTED and CONTESTED."""
        assert EvaluationStatus.DRAFT.is_finalized() is False
        assert EvaluationStatus.COMPLETED.is_finalized() is False
        assert EvaluationStatus.ACCEPTED.is_finalized() is True
        assert EvaluationStatus.CONTESTED.is_finalized() is True

    def test_can_be_submitted(self) -> None:
        """Verify can_be_submitted returns True only for DRAFT."""
        assert EvaluationStatus.DRAFT.can_be_submitted() is True
        assert EvaluationStatus.COMPLETED.can_be_submitted() is False
        assert EvaluationStatus.ACCEPTED.can_be_submitted() is False
        assert EvaluationStatus.CONTESTED.can_be_submitted() is False

    def test_can_be_responded(self) -> None:
        """Verify can_be_responded returns True only for COMPLETED."""
        assert EvaluationStatus.DRAFT.can_be_responded() is False
        assert EvaluationStatus.COMPLETED.can_be_responded() is True
        assert EvaluationStatus.ACCEPTED.can_be_responded() is False
        assert EvaluationStatus.CONTESTED.can_be_responded() is False

    def test_string_representation(self) -> None:
        """Verify enum string representation."""
        assert EvaluationStatus.DRAFT.value == "DRAFT"
        assert EvaluationStatus.COMPLETED.value == "COMPLETED"
