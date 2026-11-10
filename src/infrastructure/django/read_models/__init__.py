"""Django read model adapters backed by database views."""

from __future__ import annotations

from src.infrastructure.django.read_models.competency_history_read_model import (
    DjangoCompetencyHistoryReadModel,
)
from src.infrastructure.django.read_models.path_progression_read_model import (
    DjangoPathProgressionReadModel,
)

__all__ = [
    "DjangoCompetencyHistoryReadModel",
    "DjangoPathProgressionReadModel",
]
