"""End-to-end integration test for the complete competency management workflow.

Flow:
1. Create Category and CompetencyGroup.
2. Create Competencies in the catalog with 5 proficiency levels.
3. Define CareerPath with multiple levels and weighted competency requirements.
4. Register Collaborator and enroll them targeting a specific level.
5. Create Evaluation in draft, record measurements, submit, and accept.
6. Run Gap Analysis and confirm requirement gaps and progression eligibility.
"""

from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.competency_group import (
    CompetencyGroupModel,
)


@pytest.fixture
def client() -> APIClient:
    return APIClient()


LEVEL_DESCRIPTIONS = {
    "1": "Basic familiarity with syntax and conventions.",
    "2": "Able to write working features with guidance.",
    "3": "Independent contributor writing production-grade code.",
    "4": "Expert in architecture, performance, and best practices.",
    "5": "Industry authority driving organizational standards.",
}


@pytest.mark.django_db
def test_complete_competency_workflow(client: APIClient) -> None:
    """Validate full end-to-end user lifecycle from catalog to gap analysis."""
    # -------------------------------------------------------------------------
    # 1. Setup Hierarchy: Category and Group
    # -------------------------------------------------------------------------
    category = CategoryModel.objects.create(name="Engineering")
    group = CompetencyGroupModel.objects.create(
        name="Software Development", category=category
    )

    # -------------------------------------------------------------------------
    # 2. Create Competencies in Catalog
    # -------------------------------------------------------------------------
    python_payload = {
        "name": "Python Programming",
        "description": "Core backend language proficiency",
        "category_id": str(category.id),
        "group_id": str(group.id),
        "level_descriptions": LEVEL_DESCRIPTIONS,
    }
    python_res = client.post("/api/v1/competencies/", python_payload, format="json")
    assert python_res.status_code == status.HTTP_201_CREATED
    python_id = python_res.json()["id"]

    arch_payload = {
        "name": "System Architecture",
        "description": "Distributed systems and cloud architecture",
        "category_id": str(category.id),
        "group_id": str(group.id),
        "level_descriptions": LEVEL_DESCRIPTIONS,
    }
    arch_res = client.post("/api/v1/competencies/", arch_payload, format="json")
    assert arch_res.status_code == status.HTTP_201_CREATED
    arch_id = arch_res.json()["id"]

    # -------------------------------------------------------------------------
    # 3. Define Career Path with Ordered Levels and Requirements
    # -------------------------------------------------------------------------
    path_payload = {
        "name": "Backend Engineering Track",
        "description": "Career ladder for backend engineers",
        "levels": [
            {
                "name": "Mid-Level Engineer",
                "order": 1,
                "requirements": [
                    {
                        "competency_id": python_id,
                        "minimum_level": 3,
                        "weight": "CORE",
                    },
                    {
                        "competency_id": arch_id,
                        "minimum_level": 2,
                        "weight": "IMPORTANT",
                    },
                ],
            },
            {
                "name": "Senior Engineer",
                "order": 2,
                "requirements": [
                    {
                        "competency_id": python_id,
                        "minimum_level": 4,
                        "weight": "CORE",
                    },
                    {
                        "competency_id": arch_id,
                        "minimum_level": 3,
                        "weight": "CORE",
                    },
                ],
            },
        ],
    }
    path_res = client.post("/api/v1/paths/", path_payload, format="json")
    assert path_res.status_code == status.HTTP_201_CREATED
    path_data = path_res.json()
    path_id = path_data["id"]
    senior_level_id = path_data["levels"][1]["id"]
    assert path_data["levels"][1]["name"] == "Senior Engineer"

    # -------------------------------------------------------------------------
    # 4. Register Collaborators: Employee and Evaluator
    # -------------------------------------------------------------------------
    emp_payload = {
        "name": "João Silva",
        "email": "joao.silva@company.com",
        "department": "Platform Engineering",
    }
    emp_res = client.post("/api/v1/collaborators/", emp_payload, format="json")
    assert emp_res.status_code == status.HTTP_201_CREATED
    collaborator_id = emp_res.json()["id"]

    lead_payload = {
        "name": "Mariana Tech Lead",
        "email": "mariana.lead@company.com",
        "department": "Platform Engineering",
    }
    lead_res = client.post("/api/v1/collaborators/", lead_payload, format="json")
    assert lead_res.status_code == status.HTTP_201_CREATED
    evaluator_id = lead_res.json()["id"]

    # Enroll collaborator targeting "Senior Engineer"
    enroll_payload = {
        "path_id": path_id,
        "target_level": "Senior Engineer",
    }
    enroll_res = client.post(
        f"/api/v1/collaborators/{collaborator_id}/enroll/",
        enroll_payload,
        format="json",
    )
    assert enroll_res.status_code == status.HTTP_201_CREATED
    assert enroll_res.json()["enrollments"][0]["is_active"] is True

    # -------------------------------------------------------------------------
    # 5. Evaluation Workflow: Draft -> Measurements -> Submit -> Accept
    # -------------------------------------------------------------------------
    eval_payload = {
        "collaborator_id": collaborator_id,
        "evaluator_id": evaluator_id,
        "period": "2026.H1",
    }
    eval_create_res = client.post("/api/v1/evaluations/", eval_payload, format="json")
    assert eval_create_res.status_code == status.HTTP_201_CREATED
    evaluation_id = eval_create_res.json()["id"]
    assert eval_create_res.json()["status"] == "DRAFT"

    # Add measurement for Python: Level 4 (Meets Senior Core requirement)
    meas1_payload = {
        "competency_id": python_id,
        "current_level": 4,
        "notes": "Excellent performance writing async microservices.",
        "evidence": "PRs #204, #215",
    }
    meas1_res = client.post(
        f"/api/v1/evaluations/{evaluation_id}/measurements/",
        meas1_payload,
        format="json",
    )
    assert meas1_res.status_code == status.HTTP_201_CREATED

    # Add measurement for System Architecture: Level 3 (Meets Senior Core requirement)
    meas2_payload = {
        "competency_id": arch_id,
        "current_level": 3,
        "notes": "Designed Kafka pub-sub pipeline.",
        "evidence": "RFC 42",
    }
    meas2_res = client.post(
        f"/api/v1/evaluations/{evaluation_id}/measurements/",
        meas2_payload,
        format="json",
    )
    assert meas2_res.status_code == status.HTTP_201_CREATED

    # Submit evaluation
    submit_res = client.post(
        f"/api/v1/evaluations/{evaluation_id}/submit/", format="json"
    )
    assert submit_res.status_code == status.HTTP_200_OK
    assert submit_res.json()["status"] == "COMPLETED"

    # Accept evaluation
    accept_res = client.post(
        f"/api/v1/evaluations/{evaluation_id}/accept/",
        {"response_notes": "Agreed with evaluation results."},
        format="json",
    )
    assert accept_res.status_code == status.HTTP_200_OK
    assert accept_res.json()["status"] == "ACCEPTED"

    # -------------------------------------------------------------------------
    # 6. Gap Analysis and Progression Eligibility Check
    # -------------------------------------------------------------------------
    gap_url = (
        f"/api/v1/gap-analysis/?collaborator_id={collaborator_id}"
        f"&path_id={path_id}&level_id={senior_level_id}"
    )
    gap_res = client.get(gap_url)
    assert gap_res.status_code == status.HTTP_200_OK
    gap_data = gap_res.json()

    assert gap_data["collaborator_id"] == collaborator_id
    assert gap_data["path_id"] == path_id
    assert gap_data["level_id"] == senior_level_id

    # Check both requirements are fully met (gap = 0)
    gaps = gap_data["gaps"]
    assert len(gaps) == 2
    for gap in gaps:
        assert gap["gap"] == 0

    # Eligible for Senior promotion!
    assert gap_data["eligibility"]["is_eligible"] is True
    assert len(gap_data["eligibility"]["blocking_competency_ids"]) == 0
