"""Application ports (interfaces) defining inbound and outbound boundaries."""

from src.application.ports.competency_history_read_model import (
    CompetencyHistoryReadModel,
)
from src.application.ports.path_progression_read_model import (
    PathProgressionReadModel,
)

__all__ = [
    "CompetencyHistoryReadModel",
    "PathProgressionReadModel",
]
