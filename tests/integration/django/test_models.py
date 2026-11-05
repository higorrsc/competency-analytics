"""Integration tests for Django models and immutability constraints."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from django.db import IntegrityError, transaction

from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.domain.value_objects.requirement_weight import RequirementWeight
from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import CompetencyGroupModel
from src.infrastructure.django.models.competency_measurement import (
    CompetencyMeasurementModel,
)
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.competency_requirement import (
    CompetencyRequirementModel,
)
from src.infrastructure.django.models.evaluation import EvaluationModel
from src.infrastructure.django.models.path_enrollment import PathEnrollmentModel
from src.infrastructure.django.models.path_level import PathLevelModel

NOW = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)


def make_descriptions() -> dict[str, str]:
    """Return standard 1-5 level descriptions for testing."""
    return {
        "1": "Basic awareness",
        "2": "Guided application",
        "3": "Independent execution",
        "4": "Advanced leadership",
        "5": "Strategic mastery",
    }


@pytest.mark.django_db
class TestCompetencyHierarchyModels:
    """Tests for CategoryModel, CompetencyGroupModel, and CompetencyModel."""

    def test_should_create_hierarchy_and_display_str(self) -> None:
        """Models persist correctly and return expected __str__."""
        category = CategoryModel.objects.create(
            name="Engineering", description="Tech skills"
        )
        assert str(category) == "Engineering"

        group = CompetencyGroupModel.objects.create(
            category=category, name="Backend", description="Backend competencies"
        )
        assert str(group) == "Backend"

        competency = CompetencyModel.objects.create(
            category=category,
            group=group,
            name="Python",
            description="Core language",
            level_descriptions=make_descriptions(),
        )
        assert str(competency) == "Python"
        assert competency.level_descriptions["1"] == "Basic awareness"

    def test_should_enforce_unique_category_name(self) -> None:
        """Category names must be unique."""
        CategoryModel.objects.create(name="Architecture")
        with pytest.raises(IntegrityError):
            CategoryModel.objects.create(name="Architecture")

    def test_should_enforce_unique_group_name_per_category(self) -> None:
        """Competency groups must have unique names within the same category."""
        category1 = CategoryModel.objects.create(name="Management")
        category2 = CategoryModel.objects.create(name="Product")

        CompetencyGroupModel.objects.create(category=category1, name="Strategy")
        # Same name in different category is allowed
        CompetencyGroupModel.objects.create(category=category2, name="Strategy")

        # Duplicate in same category is rejected
        with pytest.raises(IntegrityError):
            CompetencyGroupModel.objects.create(category=category1, name="Strategy")

    def test_should_enforce_unique_competency_name_per_group(self) -> None:
        """Competencies must have unique names within the same group."""
        cat = CategoryModel.objects.create(name="Data")
        group1 = CompetencyGroupModel.objects.create(category=cat, name="Analytics")
        group2 = CompetencyGroupModel.objects.create(category=cat, name="Engineering")

        CompetencyModel.objects.create(
            category=cat,
            group=group1,
            name="SQL",
            description="Queries",
            level_descriptions=make_descriptions(),
        )
        # Same name in different group is allowed
        CompetencyModel.objects.create(
            category=cat,
            group=group2,
            name="SQL",
            description="DB dev",
            level_descriptions=make_descriptions(),
        )

        # Duplicate in same group is rejected
        with pytest.raises(IntegrityError):
            CompetencyModel.objects.create(
                category=cat,
                group=group1,
                name="SQL",
                description="Duplicate",
                level_descriptions=make_descriptions(),
            )


@pytest.mark.django_db
class TestCareerPathModels:
    """Tests for CompetencyPathModel, PathLevelModel, and CompetencyRequirementModel."""

    def test_should_create_path_levels_and_requirements(self) -> None:
        """Career path with ordered levels and weighted requirements persists."""
        category = CategoryModel.objects.create(name="Design")
        group = CompetencyGroupModel.objects.create(category=category, name="UX")
        competency = CompetencyModel.objects.create(
            category=category,
            group=group,
            name="User Research",
            description="Interviews",
            level_descriptions=make_descriptions(),
        )

        path = CompetencyPathModel.objects.create(
            name="Product Design", description="Design track"
        )
        assert str(path) == "Product Design"

        level = PathLevelModel.objects.create(path=path, name="Junior", order=1)
        assert str(level) == "Junior (L1)"

        req = CompetencyRequirementModel.objects.create(
            path_level=level,
            competency=competency,
            minimum_level=2,
            weight=RequirementWeight.CORE.value,
        )
        assert "Junior" in str(req)
        assert "User Research" in str(req)
        assert req.minimum_level == 2

    def test_should_enforce_unique_level_order_and_name_per_path(self) -> None:
        """Path levels must have unique names and orders within a path."""
        path = CompetencyPathModel.objects.create(name="Engineering")
        PathLevelModel.objects.create(path=path, name="Junior", order=1)

        # Duplicate name
        with transaction.atomic(), pytest.raises(IntegrityError):
            PathLevelModel.objects.create(path=path, name="Junior", order=2)

        # Duplicate order
        with transaction.atomic(), pytest.raises(IntegrityError):
            PathLevelModel.objects.create(path=path, name="Pleno", order=1)

    def test_should_enforce_unique_requirement_per_level(self) -> None:
        """A level cannot require the same competency multiple times."""
        category = CategoryModel.objects.create(name="Tech")
        group = CompetencyGroupModel.objects.create(category=category, name="Core")
        comp = CompetencyModel.objects.create(
            category=category,
            group=group,
            name="Git",
            description="VCS",
            level_descriptions=make_descriptions(),
        )
        path = CompetencyPathModel.objects.create(name="Developer")
        level = PathLevelModel.objects.create(path=path, name="Junior", order=1)

        CompetencyRequirementModel.objects.create(
            path_level=level,
            competency=comp,
            minimum_level=1,
            weight=RequirementWeight.CORE.value,
        )

        with pytest.raises(IntegrityError):
            CompetencyRequirementModel.objects.create(
                path_level=level,
                competency=comp,
                minimum_level=3,
                weight=RequirementWeight.IMPORTANT.value,
            )


@pytest.mark.django_db
class TestCollaboratorAndEnrollmentModels:
    """Tests for CollaboratorModel and PathEnrollmentModel."""

    def test_should_create_collaborator_and_enrollment(self) -> None:
        """Collaborator with career path enrollment persists."""
        collaborator = CollaboratorModel.objects.create(
            name="Alice", email="alice@corp.com", department="Engineering"
        )
        assert "Alice" in str(collaborator)

        path = CompetencyPathModel.objects.create(name="Backend Track")
        enrollment = PathEnrollmentModel.objects.create(
            collaborator=collaborator,
            path=path,
            target_level="Senior",
            is_active=True,
            enrolled_at=NOW,
        )
        assert "Active" in str(enrollment)
        assert enrollment.target_level == "Senior"

    def test_should_enforce_unique_email_for_collaborator(self) -> None:
        """Collaborators must have unique emails."""
        CollaboratorModel.objects.create(
            name="Bob", email="bob@corp.com", department="Sales"
        )
        with pytest.raises(IntegrityError):
            CollaboratorModel.objects.create(
                name="Bob 2", email="bob@corp.com", department="Marketing"
            )

    def test_should_enforce_unique_together_on_path_enrollment(self) -> None:
        """Collaborator cannot be enrolled in the same path multiple times."""
        collaborator = CollaboratorModel.objects.create(
            name="Charlie", email="charlie@corp.com", department="IT"
        )
        path = CompetencyPathModel.objects.create(name="DevOps")

        PathEnrollmentModel.objects.create(
            collaborator=collaborator,
            path=path,
            target_level="Junior",
            is_active=True,
            enrolled_at=NOW,
        )

        with pytest.raises(IntegrityError):
            PathEnrollmentModel.objects.create(
                collaborator=collaborator,
                path=path,
                target_level="Senior",
                is_active=False,
                enrolled_at=NOW,
            )


@pytest.mark.django_db
class TestEvaluationImmutability:
    """Tests for EvaluationModel and CompetencyMeasurementModel immutability."""

    def _setup_base(
        self,
    ) -> tuple[CollaboratorModel, CollaboratorModel, CompetencyModel]:
        collaborator = CollaboratorModel.objects.create(
            name="Employee", email="emp@corp.com", department="Dev"
        )
        evaluator = CollaboratorModel.objects.create(
            name="Manager", email="mgr@corp.com", department="Dev"
        )
        category = CategoryModel.objects.create(name="Tech")
        group = CompetencyGroupModel.objects.create(category=category, name="Core")
        comp = CompetencyModel.objects.create(
            category=category,
            group=group,
            name="Python",
            description="Language",
            level_descriptions=make_descriptions(),
        )
        return collaborator, evaluator, comp

    def test_should_allow_updating_draft_evaluation(self) -> None:
        """Draft evaluations can be modified freely."""
        collaborator, evaluator, comp = self._setup_base()
        evaluation = EvaluationModel.objects.create(
            collaborator=collaborator,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT.value,
        )
        measurement = CompetencyMeasurementModel.objects.create(
            evaluation=evaluation,
            competency=comp,
            current_level=3,
            notes="Initial notes",
        )

        # Update evaluation fields
        evaluation.period = "2026-Q1-revised"
        evaluation.save()
        evaluation.refresh_from_db()
        assert evaluation.period == "2026-Q1-revised"

        # Update measurement
        measurement.current_level = 4
        measurement.notes = "Updated notes"
        measurement.save()
        measurement.refresh_from_db()
        assert measurement.current_level == 4

    def test_should_allow_transition_to_finalized(self) -> None:
        """Evaluation can transition from completed to accepted."""
        collaborator, evaluator, _ = self._setup_base()
        evaluation = EvaluationModel.objects.create(
            collaborator=collaborator,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.COMPLETED.value,
        )

        evaluation.status = EvaluationStatus.ACCEPTED.value
        evaluation.response_notes = "Agreed with feedback"
        evaluation.save()
        evaluation.refresh_from_db()

        assert evaluation.status == EvaluationStatus.ACCEPTED.value

    def test_should_prevent_modifying_accepted_evaluation(self) -> None:
        """Accepted evaluation cannot be modified."""
        collaborator, evaluator, _ = self._setup_base()
        evaluation = EvaluationModel.objects.create(
            collaborator=collaborator,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.ACCEPTED.value,
        )

        evaluation.period = "Modified Period"
        with pytest.raises(IntegrityError, match="Cannot modify finalized evaluation"):
            evaluation.save()

    def test_should_prevent_modifying_contested_evaluation(self) -> None:
        """Contested evaluation cannot be modified."""
        collaborator, evaluator, _ = self._setup_base()
        evaluation = EvaluationModel.objects.create(
            collaborator=collaborator,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.CONTESTED.value,
            response_notes="Disagreed",
        )

        evaluation.status = EvaluationStatus.DRAFT.value
        with pytest.raises(IntegrityError, match="Cannot modify finalized evaluation"):
            evaluation.save()

    def test_should_prevent_deleting_finalized_evaluation(self) -> None:
        """Finalized evaluations cannot be deleted."""
        collaborator, evaluator, _ = self._setup_base()
        evaluation = EvaluationModel.objects.create(
            collaborator=collaborator,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.ACCEPTED.value,
        )

        with pytest.raises(IntegrityError, match="Cannot delete finalized evaluation"):
            evaluation.delete()

    def test_should_prevent_adding_or_modifying_measurements_on_finalized(self) -> None:
        """Measurements cannot be added or modified for finalized evaluations."""
        collaborator, evaluator, comp = self._setup_base()
        evaluation = EvaluationModel.objects.create(
            collaborator=collaborator,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT.value,
        )
        measurement = CompetencyMeasurementModel.objects.create(
            evaluation=evaluation,
            competency=comp,
            current_level=3,
        )

        # Finalize evaluation
        evaluation.status = EvaluationStatus.ACCEPTED.value
        evaluation.save()

        # Try to modify existing measurement
        measurement.current_level = 5
        with pytest.raises(
            IntegrityError,
            match="Cannot modify measurements of a finalized evaluation",
        ):
            measurement.save()

        # Try to delete measurement
        with pytest.raises(
            IntegrityError,
            match="Cannot delete measurements of a finalized evaluation",
        ):
            measurement.delete()

        # Try to add a new measurement to finalized evaluation
        comp2 = CompetencyModel.objects.create(
            category=comp.category,
            group=comp.group,
            name="Docker",
            description="Containers",
            level_descriptions=make_descriptions(),
        )
        new_measurement = CompetencyMeasurementModel(
            evaluation=evaluation,
            competency=comp2,
            current_level=2,
        )
        with pytest.raises(
            IntegrityError,
            match="Cannot modify measurements of a finalized evaluation",
        ):
            new_measurement.save()

    def test_should_prevent_deleting_contested_evaluation(self) -> None:
        """Contested evaluations cannot be deleted."""
        collaborator, evaluator, _ = self._setup_base()
        evaluation = EvaluationModel.objects.create(
            collaborator=collaborator,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.CONTESTED.value,
            response_notes="Contested notes",
        )

        with pytest.raises(IntegrityError, match="Cannot delete finalized evaluation"):
            evaluation.delete()

    def test_should_enforce_valid_measurement_level_range(self) -> None:
        """Measurement level must be between 1 and 5."""
        collaborator, evaluator, comp = self._setup_base()
        evaluation = EvaluationModel.objects.create(
            collaborator=collaborator,
            evaluator=evaluator,
            period="2026-Q1",
            evaluation_date=NOW,
            status=EvaluationStatus.DRAFT.value,
        )

        with transaction.atomic(), pytest.raises(IntegrityError):
            CompetencyMeasurementModel.objects.create(
                evaluation=evaluation,
                competency=comp,
                current_level=0,
            )

        with transaction.atomic(), pytest.raises(IntegrityError):
            CompetencyMeasurementModel.objects.create(
                evaluation=evaluation,
                competency=comp,
                current_level=6,
            )

    def test_should_respect_meta_ordering_across_models(self) -> None:
        """Models are retrieved in their defined default Meta ordering."""
        category_b = CategoryModel.objects.create(name="Beta Category")
        category_a = CategoryModel.objects.create(name="Alpha Category")
        assert list(CategoryModel.objects.all()) == [category_a, category_b]

        collab_b = CollaboratorModel.objects.create(
            name="Zoe", email="zoe@corp.com", department="Dev"
        )
        collab_a = CollaboratorModel.objects.create(
            name="Adam", email="adam@corp.com", department="Dev"
        )
        assert list(CollaboratorModel.objects.all()) == [collab_a, collab_b]
