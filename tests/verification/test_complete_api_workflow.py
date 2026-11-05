"""System verification test for complete API workflow execution.

Task 18.4:
- Execute complete user workflow via REST API endpoints and verify responses
  match specs.
"""

from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency_group import (
    CompetencyGroupModel,
)


@pytest.fixture
def base_catalog(db: None) -> tuple[CategoryModel, CompetencyGroupModel]:
    category = CategoryModel.objects.create(name="Software Engineering")
    group = CompetencyGroupModel.objects.create(name="Architecture", category=category)
    return category, group


@pytest.mark.django_db
def test_complete_user_workflow_via_api(
    base_catalog: tuple[CategoryModel, CompetencyGroupModel],
) -> None:
    """Execute end-to-end API user workflow from catalog setup to gap analysis."""
    client = APIClient()
    category, group = base_catalog

    # 1. Create Competencies via API
    comp1_payload = {
        "name": "Microservices Design",
        "description": "Event-driven and service architecture",
        "category_id": str(category.id),
        "group_id": str(group.id),
        "level_descriptions": {
            "1": "Monolith understanding",
            "2": "Basic API boundaries",
            "3": "Decoupled events",
            "4": "Distributed systems resilience",
            "5": "Enterprise scale leadership",
        },
    }
    r = client.post("/api/v1/competencies/", data=comp1_payload, format="json")
    assert r.status_code == status.HTTP_201_CREATED
    comp1_id = r.data["id"]

    comp2_payload = {
        "name": "Cloud Infrastructure",
        "description": "Container orchestration and IaC",
        "category_id": str(category.id),
        "group_id": str(group.id),
        "level_descriptions": {str(i): f"Level {i}" for i in range(1, 6)},
    }
    r = client.post("/api/v1/competencies/", data=comp2_payload, format="json")
    assert r.status_code == status.HTTP_201_CREATED
    comp2_id = r.data["id"]

    # 2. Create Career Path with Levels and Requirements via API
    path_payload = {
        "name": "Staff Solutions Architect",
        "description": "Senior technical track",
        "levels": [
            {
                "name": "Associate Architect",
                "order": 1,
                "requirements": [
                    {
                        "competency_id": comp1_id,
                        "minimum_level": 3,
                        "weight": "CORE",
                    },
                    {
                        "competency_id": comp2_id,
                        "minimum_level": 2,
                        "weight": "IMPORTANT",
                    },
                ],
            }
        ],
    }
    r = client.post("/api/v1/paths/", data=path_payload, format="json")
    assert r.status_code == status.HTTP_201_CREATED
    path_id = r.data["id"]
    level_id = r.data["levels"][0]["id"]

    # 3. Create Collaborator and Evaluator via API
    collab_payload = {
        "name": "Lucas Prado",
        "email": "lucas.prado@corp.com",
        "department": "Architecture",
    }
    r = client.post("/api/v1/collaborators/", data=collab_payload, format="json")
    assert r.status_code == status.HTTP_201_CREATED
    collab_id = r.data["id"]

    evaluator = CollaboratorModel.objects.create(
        name="Chief Architect",
        email="chief.architect@corp.com",
        department="Architecture",
    )

    # 4. Enroll Collaborator into Career Path via API
    enroll_payload = {
        "path_id": path_id,
        "target_level": "Associate Architect",
    }
    r = client.post(
        f"/api/v1/collaborators/{collab_id}/enroll/",
        data=enroll_payload,
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED
    assert any(
        e["path_id"] == path_id and e["is_active"] for e in r.data["enrollments"]
    )

    # 5. Create Draft Evaluation via API
    eval_payload = {
        "collaborator_id": collab_id,
        "evaluator_id": str(evaluator.id),
        "period": "2025.H1",
    }
    r = client.post("/api/v1/evaluations/", data=eval_payload, format="json")
    assert r.status_code == status.HTTP_201_CREATED
    eval_id = r.data["id"]
    assert r.data["status"] == "DRAFT"

    # Add measurements to draft evaluation via API
    m1_payload = {"competency_id": comp1_id, "current_level": 3}
    r = client.post(
        f"/api/v1/evaluations/{eval_id}/measurements/",
        data=m1_payload,
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED

    m2_payload = {"competency_id": comp2_id, "current_level": 2}
    r = client.post(
        f"/api/v1/evaluations/{eval_id}/measurements/",
        data=m2_payload,
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED

    # 6. Submit Evaluation via API
    r = client.post(f"/api/v1/evaluations/{eval_id}/submit/")
    assert r.status_code == status.HTTP_200_OK
    assert r.data["status"] == "COMPLETED"

    # 7. Accept Evaluation via API
    r = client.post(
        f"/api/v1/evaluations/{eval_id}/accept/",
        data={"notes": "All requirements verified."},
        format="json",
    )
    assert r.status_code == status.HTTP_200_OK
    assert r.data["status"] == "ACCEPTED"

    # 8. Calculate Competency Gaps via API
    gap_url = (
        f"/api/v1/gap-analysis/?collaborator_id={collab_id}"
        f"&path_id={path_id}&level_id={level_id}"
    )
    r = client.get(gap_url)
    assert r.status_code == status.HTTP_200_OK
    assert str(r.data["collaborator_id"]) == str(collab_id)
    assert r.data["eligibility"]["is_eligible"] is True
    assert len(r.data["gaps"]) == 2
    assert all(g["gap"] == 0 for g in r.data["gaps"])

    # 9. Query Longitudinal Competency History via API
    hist_url = f"/api/v1/history/?collaborator_id={collab_id}"
    r = client.get(hist_url)
    assert r.status_code == status.HTTP_200_OK
    assert len(r.data) == 2
    assert {e["competency_id"] for e in r.data} == {comp1_id, comp2_id}

    # 10. Query Path Progression Summary via API
    prog_url = f"/api/v1/progression/?collaborator_id={collab_id}&path_id={path_id}"
    r = client.get(prog_url)
    assert r.status_code == status.HTTP_200_OK
    assert r.data["collaborator_id"] == collab_id
    assert r.data["completion_percentage"] == 100.0
