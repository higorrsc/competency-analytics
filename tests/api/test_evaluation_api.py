"""Integration tests for Evaluation REST API lifecycle and measurements."""

from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import (
    CompetencyGroupModel,
)


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def test_setup(
    db: None,
) -> tuple[CollaboratorModel, CollaboratorModel, CompetencyModel]:
    collab = CollaboratorModel.objects.create(
        name="Employee", email="emp@company.com", department="Eng"
    )
    evaluator = CollaboratorModel.objects.create(
        name="Manager", email="mgr@company.com", department="Eng"
    )
    cat = CategoryModel.objects.create(name="Tech")
    group = CompetencyGroupModel.objects.create(name="Dev", category=cat)
    comp = CompetencyModel.objects.create(
        name="Python",
        description="Backend",
        category=cat,
        group=group,
        level_descriptions={
            "1": "L1",
            "2": "L2",
            "3": "L3",
            "4": "L4",
            "5": "L5",
        },
    )
    return collab, evaluator, comp


@pytest.mark.django_db
def test_evaluation_lifecycle_submit_and_accept(
    client: APIClient,
    test_setup: tuple[CollaboratorModel, CollaboratorModel, CompetencyModel],
) -> None:
    collab, evaluator, comp = test_setup

    # 1. Create Draft
    create_payload = {
        "collaborator_id": str(collab.id),
        "evaluator_id": str(evaluator.id),
        "period": "2026.Q1",
    }
    create_res = client.post("/api/v1/evaluations/", create_payload, format="json")
    assert create_res.status_code == status.HTTP_201_CREATED
    eval_id = create_res.json()["id"]
    assert create_res.json()["status"] == "DRAFT"

    # 2. Add Measurement
    meas_payload = {
        "competency_id": str(comp.id),
        "current_level": 4,
        "notes": "Excellent skills",
        "evidence": "PR #100",
    }
    meas_res = client.post(
        f"/api/v1/evaluations/{eval_id}/measurements/",
        meas_payload,
        format="json",
    )
    assert meas_res.status_code == status.HTTP_201_CREATED
    data = meas_res.json()
    assert len(data["measurements"]) == 1
    assert data["measurements"][0]["current_level"] == 4

    # 3. Submit
    submit_res = client.post(f"/api/v1/evaluations/{eval_id}/submit/", format="json")
    assert submit_res.status_code == status.HTTP_200_OK
    assert submit_res.json()["status"] == "COMPLETED"

    # 4. Attempt to add measurement to submitted evaluation (MUST FAIL 409)
    meas2_res = client.post(
        f"/api/v1/evaluations/{eval_id}/measurements/",
        meas_payload,
        format="json",
    )
    assert meas2_res.status_code == status.HTTP_409_CONFLICT

    # 5. Accept
    accept_res = client.post(
        f"/api/v1/evaluations/{eval_id}/accept/",
        {"response_notes": "Agreed with score"},
        format="json",
    )
    assert accept_res.status_code == status.HTTP_200_OK
    assert accept_res.json()["status"] == "ACCEPTED"
    assert accept_res.json()["response_notes"] == "Agreed with score"


@pytest.mark.django_db
def test_evaluation_lifecycle_contest_with_notes(
    client: APIClient,
    test_setup: tuple[CollaboratorModel, CollaboratorModel, CompetencyModel],
) -> None:
    collab, evaluator, comp = test_setup

    create_res = client.post(
        "/api/v1/evaluations/",
        {
            "collaborator_id": str(collab.id),
            "evaluator_id": str(evaluator.id),
            "period": "2026.Q1",
        },
        format="json",
    )
    eval_id = create_res.json()["id"]

    client.post(
        f"/api/v1/evaluations/{eval_id}/measurements/",
        {"competency_id": str(comp.id), "current_level": 2},
        format="json",
    )
    client.post(f"/api/v1/evaluations/{eval_id}/submit/", format="json")

    # Contest without notes -> MUST FAIL 400
    fail_res = client.post(
        f"/api/v1/evaluations/{eval_id}/contest/",
        {"response_notes": ""},
        format="json",
    )
    assert fail_res.status_code == status.HTTP_400_BAD_REQUEST

    # Contest with valid notes -> SUCCESS 200
    contest_res = client.post(
        f"/api/v1/evaluations/{eval_id}/contest/",
        {"response_notes": "I delivered advanced features this quarter"},
        format="json",
    )
    assert contest_res.status_code == status.HTTP_200_OK
    assert contest_res.json()["status"] == "CONTESTED"
    assert (
        contest_res.json()["response_notes"]
        == "I delivered advanced features this quarter"
    )


@pytest.mark.django_db
def test_submit_empty_evaluation_fails(
    client: APIClient,
    test_setup: tuple[CollaboratorModel, CollaboratorModel, CompetencyModel],
) -> None:
    collab, evaluator, _ = test_setup
    create_res = client.post(
        "/api/v1/evaluations/",
        {
            "collaborator_id": str(collab.id),
            "evaluator_id": str(evaluator.id),
            "period": "2026.Q1",
        },
        format="json",
    )
    eval_id = create_res.json()["id"]

    # Submit without measurements fails 400
    res = client.post(f"/api/v1/evaluations/{eval_id}/submit/", format="json")
    assert res.status_code == status.HTTP_400_BAD_REQUEST
