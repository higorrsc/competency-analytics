"""Integration tests for Collaborator REST API endpoints and path enrollment."""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.path_level import PathLevelModel


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def two_paths(db: None) -> tuple[CompetencyPathModel, CompetencyPathModel]:
    p1 = CompetencyPathModel.objects.create(name="Backend Track", description="BE")
    PathLevelModel.objects.create(path=p1, name="Junior", order=1)
    PathLevelModel.objects.create(path=p1, name="Senior", order=2)

    p2 = CompetencyPathModel.objects.create(name="Management Track", description="MGT")
    PathLevelModel.objects.create(path=p2, name="Lead", order=1)
    return p1, p2


@pytest.mark.django_db
def test_create_and_retrieve_collaborator(client: APIClient) -> None:
    payload = {
        "name": "Maria Santos",
        "email": "maria.santos@company.com",
        "department": "Engineering",
    }
    create_res = client.post("/api/v1/collaborators/", payload, format="json")
    assert create_res.status_code == status.HTTP_201_CREATED
    data = create_res.json()
    assert data["name"] == "Maria Santos"
    assert data["email"] == "maria.santos@company.com"
    collab_id = data["id"]

    get_res = client.get(f"/api/v1/collaborators/{collab_id}/")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == collab_id


@pytest.mark.django_db
def test_create_collaborator_duplicate_email_returns_conflict(
    client: APIClient,
) -> None:
    CollaboratorModel.objects.create(
        name="Existing User",
        email="dup@company.com",
        department="Engineering",
    )
    payload = {
        "name": "Second User",
        "email": "dup@company.com",
        "department": "Design",
    }
    res = client.post("/api/v1/collaborators/", payload, format="json")
    assert res.status_code == status.HTTP_409_CONFLICT
    assert res.json()["code"] == "conflict"


@pytest.mark.django_db
def test_enroll_collaborator_in_career_path(
    client: APIClient,
    two_paths: tuple[CompetencyPathModel, CompetencyPathModel],
) -> None:
    p1, _ = two_paths
    collab = CollaboratorModel.objects.create(
        name="Carlos",
        email="carlos@company.com",
        department="Engineering",
    )

    payload = {
        "path_id": str(p1.id),
        "target_level": "Senior",
    }
    enroll_res = client.post(
        f"/api/v1/collaborators/{collab.id}/enroll/",
        payload,
        format="json",
    )
    assert enroll_res.status_code == status.HTTP_201_CREATED
    data = enroll_res.json()
    assert len(data["enrollments"]) == 1
    enrollment = data["enrollments"][0]
    assert enrollment["path_id"] == str(p1.id)
    assert enrollment["target_level"] == "Senior"
    assert enrollment["is_active"] is True


@pytest.mark.django_db
def test_re_enrollment_in_same_path_returns_conflict(
    client: APIClient,
    two_paths: tuple[CompetencyPathModel, CompetencyPathModel],
) -> None:
    p1, _ = two_paths
    collab = CollaboratorModel.objects.create(
        name="Carlos",
        email="carlos2@company.com",
        department="Engineering",
    )
    payload = {"path_id": str(p1.id), "target_level": "Junior"}
    client.post(f"/api/v1/collaborators/{collab.id}/enroll/", payload, format="json")

    # Re-enroll
    res = client.post(
        f"/api/v1/collaborators/{collab.id}/enroll/", payload, format="json"
    )
    assert res.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
def test_activate_path_enrollment_deactivates_previous(
    client: APIClient,
    two_paths: tuple[CompetencyPathModel, CompetencyPathModel],
) -> None:
    p1, p2 = two_paths
    collab = CollaboratorModel.objects.create(
        name="Carlos",
        email="carlos3@company.com",
        department="Engineering",
    )

    # Enroll in p1 (becomes active)
    client.post(
        f"/api/v1/collaborators/{collab.id}/enroll/",
        {"path_id": str(p1.id), "target_level": "Junior"},
        format="json",
    )
    # Enroll in p2 (becomes active, p1 deactivated)
    client.post(
        f"/api/v1/collaborators/{collab.id}/enroll/",
        {"path_id": str(p2.id), "target_level": "Lead"},
        format="json",
    )

    # Now reactivate p1 via custom action
    activate_res = client.post(
        f"/api/v1/collaborators/{collab.id}/activate-path/",
        {"path_id": str(p1.id)},
        format="json",
    )
    assert activate_res.status_code == status.HTTP_200_OK
    enrollments = activate_res.json()["enrollments"]
    assert len(enrollments) == 2

    p1_enr = next(e for e in enrollments if e["path_id"] == str(p1.id))
    p2_enr = next(e for e in enrollments if e["path_id"] == str(p2.id))

    assert p1_enr["is_active"] is True
    assert p2_enr["is_active"] is False


@pytest.mark.django_db
def test_activate_nonexistent_enrollment_returns_not_found(
    client: APIClient,
) -> None:
    collab = CollaboratorModel.objects.create(
        name="Carlos",
        email="carlos4@company.com",
        department="Engineering",
    )
    res = client.post(
        f"/api/v1/collaborators/{collab.id}/activate-path/",
        {"path_id": str(uuid4())},
        format="json",
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND
