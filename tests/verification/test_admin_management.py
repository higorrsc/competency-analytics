"""System verification tests for Django Admin model management and data creation.

Tasks 18.2 & 18.3:
- Access Django admin and verify all models are manageable.
- Create sample data via admin and verify data persists correctly.
"""

from __future__ import annotations

import json

import pytest
from django.contrib.auth.models import User
from django.test.client import Client

from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import (
    CompetencyGroupModel,
)
from src.infrastructure.django.models.competency_path import CompetencyPathModel


@pytest.fixture
def admin_client() -> Client:
    """Create a client logged in as superuser."""
    admin_user = User.objects.create_superuser(
        username="superadmin",
        email="superadmin@corp.com",
        password="securepass123",
    )
    client = Client()
    client.force_login(admin_user)
    return client


@pytest.mark.django_db
def test_all_models_manageable_via_admin_views(admin_client: Client) -> None:
    """Task 18.2: Verify all model change and add pages render successfully."""
    models_to_verify = [
        "categorymodel",
        "competencygroupmodel",
        "competencymodel",
        "competencypathmodel",
        "pathlevelmodel",
        "collaboratormodel",
        "pathenrollmentmodel",
        "evaluationmodel",
    ]

    for model_name in models_to_verify:
        add_url = f"/admin/competency/{model_name}/add/"
        response = admin_client.get(add_url)
        assert response.status_code == 200, (
            f"Failed to load add page for {model_name} at {add_url}"
        )


@pytest.mark.django_db
def test_create_sample_data_via_admin_and_verify_persistence(
    admin_client: Client,
) -> None:
    """Task 18.3: Create sample domain entities via Admin and verify DB persistence."""
    # 1. Create Category via Admin
    category_data = {
        "name": "Cloud Architecture",
        "description": "AWS, GCP, and cloud platforms",
    }
    resp = admin_client.post(
        "/admin/competency/categorymodel/add/",
        data=category_data,
        follow=True,
    )
    assert resp.status_code == 200
    category = CategoryModel.objects.get(name="Cloud Architecture")
    assert category.description == "AWS, GCP, and cloud platforms"

    # 2. Create CompetencyGroup via Admin
    group_data = {
        "name": "Security & Identity",
        "category": str(category.id),
    }
    resp = admin_client.post(
        "/admin/competency/competencygroupmodel/add/",
        data=group_data,
        follow=True,
    )
    assert resp.status_code == 200
    group = CompetencyGroupModel.objects.get(name="Security & Identity")
    assert group.category == category

    # 3. Create Competency via Admin
    competency_data = {
        "name": "IAM & Policy Governance",
        "description": "Least privilege, RBAC, ABAC",
        "category": str(category.id),
        "group": str(group.id),
        "level_descriptions": json.dumps(
            {
                "1": "Basic users and roles",
                "2": "Policy authoring",
                "3": "Cross-account roles",
                "4": "Service control policies",
                "5": "Identity architecture mastery",
            }
        ),
    }
    resp = admin_client.post(
        "/admin/competency/competencymodel/add/",
        data=competency_data,
        follow=True,
    )
    assert resp.status_code == 200
    competency = CompetencyModel.objects.get(name="IAM & Policy Governance")
    assert competency.group == group
    assert "1" in competency.level_descriptions

    # 4. Create Collaborator via Admin (with formset management fields)
    collab_data = {
        "name": "Felipe Souza",
        "email": "felipe.souza@corp.com",
        "department": "Security Operations",
        "enrollments-TOTAL_FORMS": "0",
        "enrollments-INITIAL_FORMS": "0",
        "enrollments-MIN_NUM_FORMS": "0",
        "enrollments-MAX_NUM_FORMS": "1000",
    }
    resp = admin_client.post(
        "/admin/competency/collaboratormodel/add/",
        data=collab_data,
        follow=True,
    )
    assert resp.status_code == 200
    collab = CollaboratorModel.objects.get(email="felipe.souza@corp.com")
    assert collab.name == "Felipe Souza"

    # 5. Create Career Path via Admin (with formset management fields)
    path_data = {
        "name": "Cloud Security Specialist",
        "description": "SecOps track",
        "levels-TOTAL_FORMS": "0",
        "levels-INITIAL_FORMS": "0",
        "levels-MIN_NUM_FORMS": "0",
        "levels-MAX_NUM_FORMS": "1000",
    }
    resp = admin_client.post(
        "/admin/competency/competencypathmodel/add/",
        data=path_data,
        follow=True,
    )
    assert resp.status_code == 200
    path = CompetencyPathModel.objects.get(name="Cloud Security Specialist")
    assert path.description == "SecOps track"
