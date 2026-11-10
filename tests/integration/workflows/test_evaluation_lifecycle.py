"""Integration tests for evaluation lifecycle and immutability enforcement.

Tasks 16.2 & 16.3:
- 16.2: draft → add measurements → submit → accept, verify immutability enforced
- 16.3: draft → submit → contest, verify contestation notes required
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from django.db import IntegrityError

from src.application.dto.evaluation import (
    EvaluationCreateDTO,
    MeasurementCreateDTO,
)
from src.application.use_cases.errors import ConflictError, ValidationError
from src.domain.value_objects.evaluation_id import EvaluationId
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import (
    CompetencyGroupModel,
)
from src.infrastructure.django.models.competency_measurement import (
    CompetencyMeasurementModel,
)
from src.presentation.dependencies.container import get_container


@pytest.fixture
def test_setup(
    db: None,
) -> tuple[CollaboratorModel, CollaboratorModel, CompetencyModel]:
    collab = CollaboratorModel.objects.create(
        name="Alice Employee", email="alice@company.com", department="Backend"
    )
    evaluator = CollaboratorModel.objects.create(
        name="Bob Manager", email="bob@company.com", department="Backend"
    )
    cat = CategoryModel.objects.create(name="Tech")
    group = CompetencyGroupModel.objects.create(name="Core", category=cat)
    comp = CompetencyModel.objects.create(
        name="Python",
        description="Backend language",
        category=cat,
        group=group,
        level_descriptions={str(i): f"Level {i}" for i in range(1, 6)},
    )
    return collab, evaluator, comp


@pytest.mark.django_db
def test_evaluation_lifecycle_draft_to_accepted_and_immutability(
    test_setup: tuple[CollaboratorModel, CollaboratorModel, CompetencyModel],
) -> None:
    """Validate draft -> measurements -> submit -> accept and immutability."""
    collab, evaluator, comp = test_setup
    container = get_container()

    # 1. Create Draft
    create_dto = EvaluationCreateDTO(
        collaborator_id=collab.id,
        evaluator_id=evaluator.id,
        period="2026.Q1",
        evaluation_date=datetime.now(UTC),
    )
    eval_dto = container.create_evaluation_use_case.execute(create_dto)
    eval_id = EvaluationId(eval_dto.id)
    assert eval_dto.status == EvaluationStatus.DRAFT

    # 2. Add Measurement while in Draft
    meas_dto = MeasurementCreateDTO(
        competency_id=comp.id,
        current_level=4,
        notes="Solid architecture and unit test coverage",
        evidence="Merged 15 pull requests",
    )
    updated_eval = container.add_measurement_to_evaluation_use_case.execute(
        eval_id, meas_dto
    )
    assert len(updated_eval.measurements) == 1
    assert updated_eval.measurements[0].current_level == 4

    # 3. Submit Evaluation (transitions DRAFT -> COMPLETED)
    completed_eval = container.submit_evaluation_use_case.execute(eval_id)
    assert completed_eval.status == EvaluationStatus.COMPLETED

    # Verify adding measurement to completed evaluation is blocked at application layer
    with pytest.raises(ConflictError, match="immutable"):
        container.add_measurement_to_evaluation_use_case.execute(eval_id, meas_dto)

    # 4. Accept Evaluation (transitions COMPLETED -> ACCEPTED)
    final_eval = container.accept_evaluation_use_case.execute(
        eval_id, response_notes="I agree with the assessment."
    )
    assert final_eval.status == EvaluationStatus.ACCEPTED
    assert final_eval.response_notes == "I agree with the assessment."

    # 5. Verify Immutability Enforcement at Database / ORM Level
    # Adding measurement to finalized evaluation raises IntegrityError
    with pytest.raises(
        IntegrityError, match="Cannot modify measurements of a finalized"
    ):
        CompetencyMeasurementModel.objects.create(
            evaluation_id=eval_id.value,
            competency=comp,
            current_level=5,
        )

    # Saving modifications directly via repository raises IntegrityError
    loaded_eval = container.evaluation_repository.get_by_id(eval_id)
    assert loaded_eval is not None
    with pytest.raises(IntegrityError, match="Cannot modify finalized evaluation"):
        container.evaluation_repository.save(loaded_eval)


@pytest.mark.django_db
def test_evaluation_lifecycle_contested_requires_notes_and_enforces_immutability(
    test_setup: tuple[CollaboratorModel, CollaboratorModel, CompetencyModel],
) -> None:
    """Validate contestation flow requiring notes and post-finalization immutability."""
    collab, evaluator, comp = test_setup
    container = get_container()

    # Create Draft and add measurement
    create_dto = EvaluationCreateDTO(
        collaborator_id=collab.id,
        evaluator_id=evaluator.id,
        period="2026.Q1",
        evaluation_date=datetime.now(UTC),
    )
    eval_dto = container.create_evaluation_use_case.execute(create_dto)
    eval_id = EvaluationId(eval_dto.id)

    container.add_measurement_to_evaluation_use_case.execute(
        eval_id,
        MeasurementCreateDTO(competency_id=comp.id, current_level=2),
    )
    container.submit_evaluation_use_case.execute(eval_id)

    # Contesting without notes fails validation
    with pytest.raises(ValidationError, match=r"[Nn]otes"):
        container.contest_evaluation_use_case.execute(eval_id, response_notes="   ")

    # Contesting with notes transitions to CONTESTED
    contested_eval = container.contest_evaluation_use_case.execute(
        eval_id,
        response_notes="I led the refactoring project and deserve Level 3.",
    )
    assert contested_eval.status == EvaluationStatus.CONTESTED
    assert (
        contested_eval.response_notes
        == "I led the refactoring project and deserve Level 3."
    )

    # Verify immutability on CONTESTED state
    with pytest.raises(
        IntegrityError, match="Cannot modify measurements of a finalized"
    ):
        CompetencyMeasurementModel.objects.create(
            evaluation_id=eval_id.value,
            competency=comp,
            current_level=3,
        )
