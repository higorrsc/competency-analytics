"""ProgressionEligibility value object for gap analysis results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from src.domain.exceptions.gap_analysis_errors import GapAnalysisError
from src.domain.value_objects.competency_id import CompetencyId


@dataclass(frozen=True)
class ProgressionEligibility:
    """
    Whether a collaborator can progress to a target career level.

    Eligibility depends only on CORE requirements: any open CORE gap blocks
    progression, while IMPORTANT and DESIRABLE gaps do not. When the
    collaborator is not eligible, ``blocking_competency_ids`` lists the CORE
    competencies that must be developed first, preserving gap priority order.
    """

    is_eligible: bool
    blocking_competency_ids: tuple[CompetencyId, ...] = ()

    def __post_init__(self) -> None:
        """Validate the eligibility invariants after construction."""
        if not isinstance(cast(object, self.is_eligible), bool):
            raise GapAnalysisError(
                f"is_eligible must be a bool, got {type(self.is_eligible).__name__}"
            )
        self._validate_blockers(self.blocking_competency_ids)

        if self.is_eligible and self.blocking_competency_ids:
            raise GapAnalysisError(
                "An eligible collaborator cannot have blocking competencies"
            )
        if not self.is_eligible and not self.blocking_competency_ids:
            raise GapAnalysisError(
                "An ineligible collaborator must have at least one blocker"
            )

    @staticmethod
    def _validate_blockers(blockers: object) -> None:
        """
        Validate that blockers are a tuple of unique CompetencyIds.

        Args:
            blockers: Proposed blocking competency identifiers.

        Raises:
            GapAnalysisError: If the value is not a tuple, contains
                non-CompetencyId items, or repeats a competency.
        """
        if not isinstance(blockers, tuple):
            raise GapAnalysisError(
                "Blocking competency ids must be a tuple of CompetencyId"
            )

        seen: set[CompetencyId] = set()
        for blocker in cast(tuple[object, ...], blockers):
            if not isinstance(blocker, CompetencyId):
                raise GapAnalysisError(
                    "Blocking competency ids must be CompetencyId instances"
                )
            if blocker in seen:
                raise GapAnalysisError(f"Duplicate blocking competency {blocker}")
            seen.add(blocker)

    def has_blockers(self) -> bool:
        """
        Return whether at least one CORE competency blocks progression.

        Returns:
            ``True`` when blockers are present.
        """
        return bool(self.blocking_competency_ids)

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"ProgressionEligibility(is_eligible={self.is_eligible}, "
            f"blocking_competency_ids={self.blocking_competency_ids!r})"
        )
