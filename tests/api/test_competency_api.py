"""Integration tests for Competency REST API endpoints."""

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
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.competency_requirement import (
    CompetencyRequirementModel,
)
from src.infrastructure.django.models.path_level import PathLevelModel


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def category_and_group(db: None) -> tuple[CategoryModel, CompetencyGroupModel]:
    category = CategoryModel.objects.create(name="Engineering")
    group = CompetencyGroupModel.objects.create(name="Backend", category=category)
    return category, group


LEVEL_DESCRIPTIONS = {
    "1": "Awareness",
    "2": "Basic",
    "3": "Competent",
    "4": "Proficient",
    "5": "Expert",
}


@pytest.mark.django_db
def test_create_competency_success(
    client: APIClient,
    category_and_group: tuple[CategoryModel, CompetencyGroupModel],
) -> None:
    category, group = category_and_group
    payload = {
        "name": "Python",
        "description": "Backend language",
        "category_id": str(category.id),
        "group_id": str(group.id),
        "level_descriptions": LEVEL_DESCRIPTIONS,
    }

    response = client.post("/api/v1/competencies/", payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Python"
    assert data["category_id"] == str(category.id)
    assert data["group_id"] == str(group.id)
    assert len(data["level_descriptions"]) == 5


@pytest.mark.django_db
def test_create_competency_validation_error(
    client: APIClient,
    category_and_group: tuple[CategoryModel, CompetencyGroupModel],
) -> None:
    category, group = category_and_group
    # Missing level 5
    invalid_levels = {
        "1": "Awareness",
        "2": "Basic",
        "3": "Competent",
        "4": "Proficient",
    }
    payload = {
        "name": "Python",
        "description": "Backend language",
        "category_id": str(category.id),
        "group_id": str(group.id),
        "level_descriptions": invalid_levels,
    }

    response = client.post("/api/v1/competencies/", payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_list_and_retrieve_competencies(
    client: APIClient,
    category_and_group: tuple[CategoryModel, CompetencyGroupModel],
) -> None:
    category, group = category_and_group
    payload = {
        "name": "Python",
        "description": "Backend language",
        "category_id": str(category.id),
        "group_id": str(group.id),
        "level_descriptions": LEVEL_DESCRIPTIONS,
    }
    create_res = client.post("/api/v1/competencies/", payload, format="json")
    comp_id = create_res.json()["id"]

    # List
    list_res = client.get("/api/v1/competencies/")
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.json()) >= 1

    # Filtered list
    filtered_res = client.get(
        f"/api/v1/competencies/?category_id={category.id}&group_id={group.id}"
    )
    assert filtered_res.status_code == status.HTTP_200_OK
    assert len(filtered_res.json()) == 1

    # Retrieve
    get_res = client.get(f"/api/v1/competencies/{comp_id}/")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == comp_id


@pytest.mark.django_db
def test_retrieve_competency_not_found(client: APIClient) -> None:
    missing_id = uuid4()
    response = client.get(f"/api/v1/competencies/{missing_id}/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["code"] == "not_found"


@pytest.mark.django_db
def test_delete_unreferenced_competency(
    client: APIClient,
    category_and_group: tuple[CategoryModel, CompetencyGroupModel],
) -> None:
    category, group = category_and_group
    payload = {
        "name": "Go",
        "description": "Cloud language",
        "category_id": str(category.id),
        "group_id": str(group.id),
        "level_descriptions": LEVEL_DESCRIPTIONS,
    }
    create_res = client.post("/api/v1/competencies/", payload, format="json")
    comp_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/competencies/{comp_id}/")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    get_res = client.get(f"/api/v1/competencies/{comp_id}/")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_referenced_competency_returns_conflict(
    client: APIClient,
    category_and_group: tuple[CategoryModel, CompetencyGroupModel],
) -> None:
    category, group = category_and_group
    comp_model = CompetencyModel.objects.create(
        name="Rust",
        description="Systems",
        category=category,
        group=group,
        level_descriptions=LEVEL_DESCRIPTIONS,
    )
    path_model = CompetencyPathModel.objects.create(
        name="Systems Track", description="Track"
    )
    level_model = PathLevelModel.objects.create(path=path_model, name="L1", order=1)
    CompetencyRequirementModel.objects.create(
        path_level=level_model,
        competency=comp_model,
        minimum_level=3,
        weight="CORE",
    )

    del_res = client.delete(f"/api/v1/competencies/{comp_model.id}/")
    assert del_res.status_code == status.HTTP_409_CONFLICT
    assert del_res.json()["code"] == "conflict"
