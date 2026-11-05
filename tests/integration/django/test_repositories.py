"""Integration tests for Django repository implementations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.domain.entities.collaborator import Collaborator
from src.domain.entities.competency import Competency
from src.domain.entities.competency_measurement import CompetencyMeasurement
from src.domain.entities.competency_path import CompetencyPath
from src.domain.entities.evaluation import Evaluation
from src.domain.entities.path_level import PathLevel
from src.domain.exceptions.competency_errors import CompetencyReferencedError
from src.domain.repositories.collaborator_repository import CollaboratorRepository
from src.domain.repositories.competency_repository import CompetencyRepository
from src.domain.repositories.evaluation_repository import EvaluationRepository
from src.domain.repositories.path_repository import PathRepository
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.competency_requirement import CompetencyRequirement
from src.domain.value_objects.evaluation_id import EvaluationId
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.domain.value_objects.group_id import GroupId
from src.domain.value_objects.level_id import LevelId
from src.domain.value_objects.measurement_id import MeasurementId
from src.domain.value_objects.path_enrollment import PathEnrollment
from src.domain.value_objects.path_id import PathId
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
from src.infrastructure.django.repositories.collaborator_repository import (
    DjangoCollaboratorRepository,
)
from src.infrastructure.django.repositories.competency_repository import (
    DjangoCompetencyRepository,
)
from src.infrastructure.django.repositories.evaluation_repository import (
    DjangoEvaluationRepository,
)
from src.infrastructure.django.repositories.path_repository import (
    DjangoPathRepository,
)

NOW = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)


def make_descriptions() -> dict[int, str]:
    """Return standard 1-5 level descriptions for testing."""
    return {
        1: "Basic awareness",
        2: "Guided application",
        3: "Independent execution",
        4: "Advanced leadership",
        5: "Strategic mastery",
    }


def make_competency(
    *,
    competency_id: CompetencyId | None = None,
    category_id: CategoryId | None = None,
    group_id: GroupId | None = None,
    name: str = "Python Programming",
) -> Competency:
    """Helper to create a valid domain Competency entity."""
    return Competency(
        id=competency_id or CompetencyId.generate(),
        name=name,
        description="Core language skills",
        category_id=category_id or CategoryId.generate(),
        group_id=group_id or GroupId.generate(),
        level_descriptions=make_descriptions(),
    )


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

        # Create a path referencing this competency
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

    def test_should_prevent_deleting_competency_referenced_by_evaluation(self) -> None:
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


@pytest.mark.django_db
class TestDjangoPathRepository:
    """Tests for DjangoPathRepository implementing PathRepository."""

    def test_should_satisfy_protocol(self) -> None:
        """Repository satisfies the domain protocol."""
        repo = DjangoPathRepository()
        assert isinstance(repo, PathRepository)

    def test_should_save_and_retrieve_path_with_levels_and_requirements(self) -> None:
        """Career path with nested levels and requirements persists completely."""
        # Ensure competency exists in DB for foreign key constraint
        comp_repo = DjangoCompetencyRepository()
        comp = make_competency(name="Architecture")
        comp_repo.save(comp)

        repo = DjangoPathRepository()
        path = CompetencyPath(
            id=PathId.generate(),
            name="Software Engineering",
            description="Engineering career track",
            levels=[
                PathLevel(
                    id=LevelId.generate(),
                    name="Junior",
                    order=1,
                    requirements=[
                        CompetencyRequirement(
                            competency_id=comp.id,
                            minimum_level=2,
                            weight=RequirementWeight.CORE,
                        )
                    ],
                ),
                PathLevel(
                    id=LevelId.generate(),
                    name="Pleno",
                    order=2,
                    requirements=[
                        CompetencyRequirement(
                            competency_id=comp.id,
                            minimum_level=3,
                            weight=RequirementWeight.IMPORTANT,
                        )
                    ],
                ),
            ],
        )

        repo.save(path)
        loaded = repo.get_by_id(path.id)

        assert loaded is not None
        assert isinstance(loaded, CompetencyPath)
        assert loaded.id == path.id
        assert loaded.name == "Software Engineering"
        assert len(loaded.levels) == 2
        assert loaded.levels[0].name == "Junior"
        assert loaded.levels[0].order == 1
        assert len(loaded.levels[0].requirements) == 1
        assert loaded.levels[0].requirements[0].competency_id == comp.id
        assert loaded.levels[0].requirements[0].minimum_level == 2
        assert loaded.levels[0].requirements[0].weight == RequirementWeight.CORE

        assert loaded.levels[1].name == "Pleno"
        assert loaded.levels[1].requirements[0].minimum_level == 3
        assert loaded.levels[1].requirements[0].weight == RequirementWeight.IMPORTANT

    def test_should_update_path_levels_synchronization(self) -> None:
        """Saving a path synchronizes updated, added, and removed levels."""
        comp_repo = DjangoCompetencyRepository()
        comp = make_competency()
        comp_repo.save(comp)

        repo = DjangoPathRepository()
        path = CompetencyPath(
            id=PathId.generate(),
            name="Initial Path",
            description="Desc",
            levels=[
                PathLevel(
                    id=LevelId.generate(),
                    name="Level 1",
                    order=1,
                    requirements=[],
                )
            ],
        )
        repo.save(path)

        # Update path: add Level 2, rename Level 1
        path.levels[0].name = "Junior"
        path.levels.append(
            PathLevel(
                id=LevelId.generate(),
                name="Mid",
                order=2,
                requirements=[
                    CompetencyRequirement(
                        competency_id=comp.id,
                        minimum_level=3,
                        weight=RequirementWeight.DESIRABLE,
                    )
                ],
            )
        )
        repo.save(path)

        loaded = repo.get_by_id(path.id)
        assert loaded is not None
        assert len(loaded.levels) == 2
        assert loaded.levels[0].name == "Junior"
        assert loaded.levels[1].name == "Mid"
        assert len(loaded.levels[1].requirements) == 1

    def test_should_find_all_paths(self) -> None:
        """All paths are returned."""
        repo = DjangoPathRepository()
        p1 = CompetencyPath(id=PathId.generate(), name="Path A", description="D1")
        p2 = CompetencyPath(id=PathId.generate(), name="Path B", description="D2")
        repo.save(p1)
        repo.save(p2)

        all_paths = repo.find_all()
        assert len(all_paths) == 2
        assert [p.name for p in all_paths] == ["Path A", "Path B"]


@pytest.mark.django_db
class TestDjangoCollaboratorRepository:
    """Tests for DjangoCollaboratorRepository implementing CollaboratorRepository."""

    def test_should_satisfy_protocol(self) -> None:
        """Repository satisfies the domain protocol."""
        repo = DjangoCollaboratorRepository()
        assert isinstance(repo, CollaboratorRepository)

    def test_should_save_and_retrieve_collaborator_with_enrollments(self) -> None:
        """Collaborator persists with active and inactive path enrollments."""
        path_repo = DjangoPathRepository()
        path1 = CompetencyPath(
            id=PathId.generate(), name="Frontend Track", description=""
        )
        path2 = CompetencyPath(
            id=PathId.generate(), name="Management Track", description=""
        )
        path_repo.save(path1)
        path_repo.save(path2)

        repo = DjangoCollaboratorRepository()
        collaborator = Collaborator(
            id=CollaboratorId.generate(),
            name="Diana Prince",
            email="diana@justice.org",
            department="Operations",
            enrollments=[
                PathEnrollment(
                    path_id=path1.id,
                    target_level="Senior",
                    enrolled_at=NOW - timedelta(days=100),
                    is_active=False,
                ),
                PathEnrollment(
                    path_id=path2.id,
                    target_level="Lead",
                    enrolled_at=NOW,
                    is_active=True,
                ),
            ],
        )

        repo.save(collaborator)
        loaded = repo.get_by_id(collaborator.id)

        assert loaded is not None
        assert isinstance(loaded, Collaborator)
        assert loaded.id == collaborator.id
        assert loaded.name == "Diana Prince"
        assert loaded.email == "diana@justice.org"
        assert loaded.department == "Operations"
        assert len(loaded.enrollments) == 2

        active = loaded.active_enrollment()
        assert active is not None
        assert active.path_id == path2.id
        assert active.target_level == "Lead"

    def test_should_find_collaborators_by_path(self) -> None:
        """Find collaborators filtered by path, optionally active only."""
        path_repo = DjangoPathRepository()
        path = CompetencyPath(id=PathId.generate(), name="Data Track", description="")
        path_repo.save(path)

        repo = DjangoCollaboratorRepository()
        c1 = Collaborator(
            id=CollaboratorId.generate(),
            name="Active Member",
            email="active@corp.com",
            department="Data",
            enrollments=[
                PathEnrollment(
                    path_id=path.id,
                    target_level="Mid",
                    enrolled_at=NOW,
                    is_active=True,
                )
            ],
        )
        c2 = Collaborator(
            id=CollaboratorId.generate(),
            name="Inactive Member",
            email="inactive@corp.com",
            department="Data",
            enrollments=[
                PathEnrollment(
                    path_id=path.id,
                    target_level="Junior",
                    enrolled_at=NOW - timedelta(days=200),
                    is_active=False,
                )
            ],
        )
        repo.save(c1)
        repo.save(c2)

        all_enrolled = repo.find_by_path(path.id, active_only=False)
        assert len(all_enrolled) == 2

        active_only = repo.find_by_path(path.id, active_only=True)
        assert len(active_only) == 1
        assert active_only[0].id == c1.id


@pytest.mark.django_db
class TestDjangoEvaluationRepository:
    """Tests for DjangoEvaluationRepository implementing EvaluationRepository."""

    def _setup_collabs_and_comp(
        self,
    ) -> tuple[Collaborator, Collaborator, Competency]:
        collab_repo = DjangoCollaboratorRepository()
        comp_repo = DjangoCompetencyRepository()

        collaborator = Collaborator(
            id=CollaboratorId.generate(),
            name="John Doe",
            email="john@corp.com",
            department="Engineering",
        )
        evaluator = Collaborator(
            id=CollaboratorId.generate(),
            name="Jane Boss",
            email="jane@corp.com",
            department="Engineering",
        )
        collab_repo.save(collaborator)
        collab_repo.save(evaluator)

        competency = make_competency()
        comp_repo.save(competency)
        return collaborator, evaluator, competency

    def test_should_satisfy_protocol(self) -> None:
        """Repository satisfies the domain protocol."""
        repo = DjangoEvaluationRepository()
        assert isinstance(repo, EvaluationRepository)

    def test_should_save_and_retrieve_evaluation_with_measurements(self) -> None:
        """Evaluation aggregate persists with measurements and dates."""
        collaborator, evaluator, competency = self._setup_collabs_and_comp()
        repo = DjangoEvaluationRepository()

        measurement = CompetencyMeasurement(
            id=MeasurementId.generate(),
            competency_id=competency.id,
            current_level=3,
            notes="Strong skills",
            evidence="PR #42",
        )
        evaluation = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collaborator.id,
            evaluator_id=evaluator.id,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT,
            measurements=[measurement],
        )

        repo.save(evaluation)
        loaded = repo.get_by_id(evaluation.id)

        assert loaded is not None
        assert isinstance(loaded, Evaluation)
        assert loaded.id == evaluation.id
        assert loaded.collaborator_id == collaborator.id
        assert loaded.evaluator_id == evaluator.id
        assert loaded.period == "2026-Q1"
        assert loaded.status == EvaluationStatus.DRAFT
        assert len(loaded.measurements) == 1
        assert loaded.measurements[0].competency_id == competency.id
        assert loaded.measurements[0].current_level == 3
        assert loaded.measurements[0].notes == "Strong skills"
        assert loaded.measurements[0].evidence == "PR #42"

    def test_should_find_latest_finalized_for_collaborator(self) -> None:
        """Queries the most recent finalized evaluation, ignoring drafts."""
        collaborator, evaluator, competency = self._setup_collabs_and_comp()
        repo = DjangoEvaluationRepository()

        # Older accepted evaluation
        older = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collaborator.id,
            evaluator_id=evaluator.id,
            period="2025-Q3",
            evaluation_date=NOW - timedelta(days=180),
            status=EvaluationStatus.ACCEPTED,
            submitted_at=NOW - timedelta(days=180),
            response_date=NOW - timedelta(days=175),
            response_notes="Agreed",
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=competency.id,
                    current_level=2,
                )
            ],
        )

        # Newer contested evaluation
        newer = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collaborator.id,
            evaluator_id=evaluator.id,
            period="2025-Q4",
            evaluation_date=NOW - timedelta(days=90),
            status=EvaluationStatus.CONTESTED,
            submitted_at=NOW - timedelta(days=90),
            response_date=NOW - timedelta(days=85),
            response_notes="Disagreed with grade",
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=competency.id,
                    current_level=3,
                )
            ],
        )

        # Even newer draft evaluation (must be ignored)
        draft = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collaborator.id,
            evaluator_id=evaluator.id,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT,
            measurements=[
                CompetencyMeasurement(
                    id=MeasurementId.generate(),
                    competency_id=competency.id,
                    current_level=4,
                )
            ],
        )

        repo.save(older)
        repo.save(newer)
        repo.save(draft)

        latest = repo.find_latest_finalized_for_collaborator(collaborator.id)
        assert latest is not None
        assert latest.id == newer.id
        assert latest.period == "2025-Q4"
        assert latest.status == EvaluationStatus.CONTESTED

    def test_should_return_none_when_no_finalized_evaluation_exists(self) -> None:
        """Returns None if collaborator only has drafts or completed evaluations."""
        collaborator, evaluator, _comp = self._setup_collabs_and_comp()
        repo = DjangoEvaluationRepository()

        draft = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=collaborator.id,
            evaluator_id=evaluator.id,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT,
        )
        repo.save(draft)

        assert repo.find_latest_finalized_for_collaborator(collaborator.id) is None
