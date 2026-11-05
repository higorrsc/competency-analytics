"""Integration tests for DjangoCompetencyRepository."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.domain.entities.competency import Competency
from src.domain.exceptions.competency_errors import CompetencyReferencedError
from src.domain.repositories.competency_repository import CompetencyRepository
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.domain.value_objects.group_id import GroupId
from src.domain.value_objects.requirement_weight import RequirementWeight
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency_measurement import (
    CompetencyMeasurementModel,
)
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.competency_requirement import (
    CompetencyRequirementModel,
)
from src.infrastructure.django.models.evaluation import EvaluationModel
from src.infrastructure.django.models.path_level import PathLevelModel
from src.infrastructure.django.repositories.competency_repository import (
    DjangoCompetencyRepository,
)
from tests.integration.django.repositories.helpers import make_competency

NOW = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)


@pytest.mark.django_db
class TestDjangoCompetencyRepository:
    """Tests for DjangoCompetencyRepository implementing CompetencyRepository."""

    def test_should_satisfy_protocol(self) -> None:
        """Repository satisfies the domain protocol."""
        repo = DjangoCompetencyRepository()
        assert isinstance(repo, CompetencyRepository)

    def test_should_save_and_retrieve_competency(self) -> None:
        """A domain competency persists and maps back with all 5 levels."""
        repo = DjangoCompetencyRepository()
        competency = make_competency()

        repo.save(competency)
        loaded = repo.get_by_id(competency.id)

        assert loaded is not None
        assert isinstance(loaded, Competency)
        assert loaded.id == competency.id
        assert loaded.name == competency.name
        assert loaded.description == competency.description
        assert loaded.category_id == competency.category_id
        assert loaded.group_id == competency.group_id
        assert loaded.level_descriptions == competency.level_descriptions

    def test_should_return_none_for_missing_competency(self) -> None:
        """Querying a missing competency returns None."""
        repo = DjangoCompetencyRepository()
        assert repo.get_by_id(CompetencyId.generate()) is None

    def test_should_update_existing_competency(self) -> None:
        """Saving an existing competency updates its stored data."""
        repo = DjangoCompetencyRepository()
        competency = make_competency(name="Original Name")
        repo.save(competency)

        competency.update_details(name="Updated Name", description="New description")
        repo.save(competency)

        loaded = repo.get_by_id(competency.id)
        assert loaded is not None
        assert loaded.name == "Updated Name"
        assert loaded.description == "New description"

    def test_should_find_by_hierarchy(self) -> None:
        """Competencies can be filtered by category and/or group."""
        repo = DjangoCompetencyRepository()
        cat1 = CategoryId.generate()
        cat2 = CategoryId.generate()
        grp1 = GroupId.generate()
        grp2 = GroupId.generate()
        grp3 = GroupId.generate()

        c1 = make_competency(category_id=cat1, group_id=grp1, name="Comp A")
        c2 = make_competency(category_id=cat1, group_id=grp2, name="Comp B")
        c3 = make_competency(category_id=cat2, group_id=grp3, name="Comp C")

        repo.save(c1)
        repo.save(c2)
        repo.save(c3)

        assert len(repo.find_by_hierarchy(category_id=cat1)) == 2
        assert len(repo.find_by_hierarchy(group_id=grp1)) == 1
        assert len(repo.find_by_hierarchy(category_id=cat1, group_id=grp1)) == 1
        assert len(repo.find_by_hierarchy()) == 3

    def test_should_delete_unreferenced_competency(self) -> None:
        """An unreferenced competency can be deleted."""
        repo = DjangoCompetencyRepository()
        competency = make_competency()
        repo.save(competency)

        repo.delete(competency.id)
        assert repo.get_by_id(competency.id) is None

    def test_should_prevent_deleting_competency_referenced_by_path(self) -> None:
        """Deleting a competency referenced in a career path raises error."""
        repo = DjangoCompetencyRepository()
        competency = make_competency()
        repo.save(competency)

        path_model = CompetencyPathModel.objects.create(name="Engineering")
        level_model = PathLevelModel.objects.create(
            path=path_model, name="Junior", order=1
        )
        CompetencyRequirementModel.objects.create(
            path_level=level_model,
            competency_id=competency.id.value,
            minimum_level=2,
            weight=RequirementWeight.CORE.value,
        )

        with pytest.raises(CompetencyReferencedError, match="career paths"):
            repo.delete(competency.id)

    def test_should_prevent_deleting_competency_referenced_by_evaluation(
        self,
    ) -> None:
        """Deleting a competency referenced in an evaluation raises error."""
        repo = DjangoCompetencyRepository()
        competency = make_competency()
        repo.save(competency)

        collab = CollaboratorModel.objects.create(
            name="Alice", email="alice@test.com", department="IT"
        )
        eval_model = EvaluationModel.objects.create(
            collaborator=collab,
            evaluator=collab,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT.value,
        )
        CompetencyMeasurementModel.objects.create(
            evaluation=eval_model,
            competency_id=competency.id.value,
            current_level=3,
        )

        with pytest.raises(CompetencyReferencedError, match="evaluations"):
            repo.delete(competency.id)
