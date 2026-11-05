"""Integration tests for Django Admin site registrations and changelists."""

from __future__ import annotations

import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.test.client import Client

from src.infrastructure.django.admin.category_admin import CategoryAdmin
from src.infrastructure.django.admin.collaborator_admin import (
    CollaboratorAdmin,
    PathEnrollmentAdmin,
)
from src.infrastructure.django.admin.competency_admin import CompetencyAdmin
from src.infrastructure.django.admin.competency_group_admin import (
    CompetencyGroupAdmin,
)
from src.infrastructure.django.admin.competency_path_admin import (
    CompetencyPathAdmin,
    PathLevelAdmin,
)
from src.infrastructure.django.admin.evaluation_admin import EvaluationAdmin
from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import CompetencyGroupModel
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.evaluation import EvaluationModel
from src.infrastructure.django.models.path_enrollment import PathEnrollmentModel
from src.infrastructure.django.models.path_level import PathLevelModel


@pytest.fixture
def admin_user() -> User:
    """Create a superuser for admin testing."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
    )


@pytest.mark.django_db
class TestDjangoAdminRegistration:
    """Verify that all domain models are properly registered in admin.site."""

    def test_should_register_all_domain_models(self) -> None:
        """All expected infrastructure models are registered in the admin registry."""
        registered = admin.site._registry
        assert CategoryModel in registered
        assert isinstance(registered[CategoryModel], CategoryAdmin)

        assert CompetencyGroupModel in registered
        assert isinstance(registered[CompetencyGroupModel], CompetencyGroupAdmin)

        assert CompetencyModel in registered
        assert isinstance(registered[CompetencyModel], CompetencyAdmin)

        assert CompetencyPathModel in registered
        assert isinstance(registered[CompetencyPathModel], CompetencyPathAdmin)

        assert PathLevelModel in registered
        assert isinstance(registered[PathLevelModel], PathLevelAdmin)

        assert CollaboratorModel in registered
        assert isinstance(registered[CollaboratorModel], CollaboratorAdmin)

        assert PathEnrollmentModel in registered
        assert isinstance(registered[PathEnrollmentModel], PathEnrollmentAdmin)

        assert EvaluationModel in registered
        assert isinstance(registered[EvaluationModel], EvaluationAdmin)

    def test_should_allow_superuser_to_access_admin_changelists(
        self, client: Client, admin_user: User
    ) -> None:
        """Superuser can access all changelist views via HTTP GET."""
        client.force_login(admin_user)

        endpoints = [
            "/admin/competency/categorymodel/",
            "/admin/competency/competencygroupmodel/",
            "/admin/competency/competencymodel/",
            "/admin/competency/competencypathmodel/",
            "/admin/competency/collaboratormodel/",
            "/admin/competency/evaluationmodel/",
        ]
        for url in endpoints:
            response = client.get(url)
            assert response.status_code == 200, f"Failed accessing {url}"
