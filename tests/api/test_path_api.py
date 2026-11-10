"""Integration tests for CareerPath REST API endpoints."""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import (
    CompetencyGroupModel,
)


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def competency(db: None) -> CompetencyModel:
    category = CategoryModel.objects.create(name="Engineering")
    group = CompetencyGroupModel.objects.create(name="Backend", category=category)
    return CompetencyModel.objects.create(
        name="Python",
        description="Backend language",
        category=category,
        group=group,
        level_descriptions={
            "1": "Awareness",
            "2": "Basic",
            "3": "Competent",
            "4": "Proficient",
            "5": "Expert",
        },
    )


@pytest.mark.django_db
def test_create_and_retrieve_career_path_complete_structure(
    client: APIClient,
    competency: CompetencyModel,
) -> None:
    payload = {
        "name": "Backend Engineer Track",
        "description": "Standard career track for backend devs",
        "levels": [
            {
                "name": "Junior",
                "order": 1,
                "requirements": [
                    {
                        "competency_id": str(competency.id),
                        "minimum_level": 2,
                        "weight": "CORE",
                    }
                ],
            },
            {
                "name": "Mid-Level",
                "order": 2,
                "requirements": [
                    {
                        "competency_id": str(competency.id),
                        "minimum_level": 3,
                        "weight": "CORE",
                    }
                ],
            },
            {
                "name": "Senior",
                "order": 3,
                "requirements": [
                    {
                        "competency_id": str(competency.id),
                        "minimum_level": 4,
                        "weight": "IMPORTANT",
                    }
                ],
            },
        ],
    }

    # Create
    create_res = client.post("/api/v1/paths/", payload, format="json")
    assert create_res.status_code == status.HTTP_201_CREATED
    data = create_res.json()
    assert data["name"] == "Backend Engineer Track"
    assert len(data["levels"]) == 3
    path_id = data["id"]

    # Retrieve
    get_res = client.get(f"/api/v1/paths/{path_id}/")
    assert get_res.status_code == status.HTTP_200_OK
    retrieved = get_res.json()
    assert retrieved["id"] == path_id
    assert len(retrieved["levels"]) == 3
    # Check levels ordering and nested requirement structure
    assert retrieved["levels"][0]["name"] == "Junior"
    assert retrieved["levels"][0]["order"] == 1
    assert len(retrieved["levels"][0]["requirements"]) == 1
    req = retrieved["levels"][0]["requirements"][0]
    assert req["competency_id"] == str(competency.id)
    assert req["minimum_level"] == 2
    assert req["weight"] == "CORE"


@pytest.mark.django_db
def test_create_career_path_rejects_non_sequential_levels(
    client: APIClient,
    competency: CompetencyModel,
) -> None:
    empty_reqs: list[dict[str, object]] = []
    payload = {
        "name": "Broken Track",
        "description": "Non-sequential levels",
        "levels": [
            {"name": "Junior", "order": 1, "requirements": empty_reqs},
            {"name": "Senior", "order": 3, "requirements": empty_reqs},  # skips 2!
        ],
    }
    response = client.post("/api/v1/paths/", payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_list_career_paths(client: APIClient, competency: CompetencyModel) -> None:
    empty_reqs: list[dict[str, object]] = []
    payload = {
        "name": "DevOps Track",
        "description": "DevOps",
        "levels": [{"name": "Associate", "order": 1, "requirements": empty_reqs}],
    }
    client.post("/api/v1/paths/", payload, format="json")

    response = client.get("/api/v1/paths/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 1


@pytest.mark.django_db
def test_retrieve_career_path_not_found(client: APIClient) -> None:
    response = client.get(f"/api/v1/paths/{uuid4()}/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
