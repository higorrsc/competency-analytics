"""Integration tests for DjangoCollaboratorRepository."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.domain.entities.collaborator import Collaborator
from src.domain.entities.competency_path import CompetencyPath
from src.domain.repositories.collaborator_repository import (
    CollaboratorRepository,
)
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_enrollment import PathEnrollment
from src.domain.value_objects.path_id import PathId
from src.infrastructure.django.repositories.collaborator_repository import (
    DjangoCollaboratorRepository,
)
from src.infrastructure.django.repositories.path_repository import (
    DjangoPathRepository,
)

NOW = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)


@pytest.mark.django_db
class TestDjangoCollaboratorRepository:
    """Tests for DjangoCollaboratorRepository implementing CollaboratorRepository."""

    def test_should_satisfy_protocol(self) -> None:
        """Repository satisfies the domain protocol."""
        repo = DjangoCollaboratorRepository()
        assert isinstance(repo, CollaboratorRepository)

    def test_should_save_and_retrieve_collaborator_with_enrollments(
        self,
    ) -> None:
        """Collaborator persists with active and inactive path enrollments."""
        path_repo = DjangoPathRepository()
        path1 = CompetencyPath(
            id=PathId.generate(), name="Frontend Track", description=""
        )
        path2 = CompetencyPath(
            id=PathId.generate(), name="Management Track", description=""
        )
        path_repo.save(path1)
        path_repo.save(path2)

        repo = DjangoCollaboratorRepository()
        collaborator = Collaborator(
            id=CollaboratorId.generate(),
            name="Diana Prince",
            email="diana@justice.org",
            department="Operations",
            enrollments=[
                PathEnrollment(
                    path_id=path1.id,
                    target_level="Senior",
                    enrolled_at=NOW - timedelta(days=100),
                    is_active=False,
                ),
                PathEnrollment(
                    path_id=path2.id,
                    target_level="Lead",
                    enrolled_at=NOW,
                    is_active=True,
                ),
            ],
        )

        repo.save(collaborator)
        loaded = repo.get_by_id(collaborator.id)

        assert loaded is not None
        assert isinstance(loaded, Collaborator)
        assert loaded.id == collaborator.id
        assert loaded.name == "Diana Prince"
        assert loaded.email == "diana@justice.org"
        assert loaded.department == "Operations"
        assert len(loaded.enrollments) == 2

        active = loaded.active_enrollment()
        assert active is not None
        assert active.path_id == path2.id
        assert active.target_level == "Lead"

    def test_should_find_collaborators_by_path(self) -> None:
        """Find collaborators filtered by path, optionally active only."""
        path_repo = DjangoPathRepository()
        path = CompetencyPath(id=PathId.generate(), name="Data Track", description="")
        path_repo.save(path)

        repo = DjangoCollaboratorRepository()
        c1 = Collaborator(
            id=CollaboratorId.generate(),
            name="Active Member",
            email="active@corp.com",
            department="Data",
            enrollments=[
                PathEnrollment(
                    path_id=path.id,
                    target_level="Mid",
                    enrolled_at=NOW,
                    is_active=True,
                )
            ],
        )
        c2 = Collaborator(
            id=CollaboratorId.generate(),
            name="Inactive Member",
            email="inactive@corp.com",
            department="Data",
            enrollments=[
                PathEnrollment(
                    path_id=path.id,
                    target_level="Junior",
                    enrolled_at=NOW - timedelta(days=200),
                    is_active=False,
                )
            ],
        )
        repo.save(c1)
        repo.save(c2)

        all_enrolled = repo.find_by_path(path.id, active_only=False)
        assert len(all_enrolled) == 2

        active_only = repo.find_by_path(path.id, active_only=True)
        assert len(active_only) == 1
        assert active_only[0].id == c1.id
