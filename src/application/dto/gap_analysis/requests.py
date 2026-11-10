"""Input request DTOs for the gap analysis application boundary."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GapAnalysisRequestDTO(BaseModel):
    """
    Input contract for requesting gap analysis.

    The target level is explicit, so callers may analyze any path level, not
    only the collaborator's currently enrolled target.
    """

    model_config = ConfigDict(frozen=True)

    collaborator_id: UUID
    path_id: UUID
    level_id: UUID
