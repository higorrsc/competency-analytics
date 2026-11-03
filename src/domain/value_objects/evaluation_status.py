"""Evaluation status enumeration representing the lifecycle states of an evaluation."""

from enum import StrEnum


class EvaluationStatus(StrEnum):
    """
    Evaluation lifecycle status.

    An evaluation progresses through these states:
    - DRAFT: Draft state, measurements can be added/modified
    - COMPLETED: Submitted for employee review, awaiting response
    - ACCEPTED: Employee accepted the evaluation, permanently immutable
    - CONTESTED: Employee contested the evaluation, permanently immutable
    """

    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
    ACCEPTED = "ACCEPTED"
    CONTESTED = "CONTESTED"

    def is_draft(self) -> bool:
        """Check if status is draft (can be modified)."""
        return self == EvaluationStatus.DRAFT

    def is_finalized(self) -> bool:
        """Check if status is finalized (immutable)."""
        return self in (EvaluationStatus.ACCEPTED, EvaluationStatus.CONTESTED)

    def can_be_submitted(self) -> bool:
        """Check if evaluation can be submitted (draft → completed)."""
        return self == EvaluationStatus.DRAFT

    def can_be_responded(self) -> bool:
        """Check if evaluation can receive employee response (accept/contest)."""
        return self == EvaluationStatus.COMPLETED
