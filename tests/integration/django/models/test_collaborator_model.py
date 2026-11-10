"""Integration tests for CollaboratorModel."""

from __future__ import annotations

import pytest
from django.db import IntegrityError

from src.infrastructure.django.models.collaborator import CollaboratorModel


@pytest.mark.django_db
class TestCollaboratorModel:
    """Tests for CollaboratorModel persistence, unique email, and ordering."""

    def test_should_create_collaborator_and_display_str(self) -> None:
        """Collaborator persists and displays name and department on __str__."""
        collaborator = CollaboratorModel.objects.create(
            name="Alice", email="alice@corp.com", department="Engineering"
        )
        assert "Alice" in str(collaborator)
        assert "Engineering" in str(collaborator)

    def test_should_enforce_unique_email_for_collaborator(self) -> None:
        """Collaborators must have unique emails."""
        CollaboratorModel.objects.create(
            name="Bob", email="bob@corp.com", department="Sales"
        )
        with pytest.raises(IntegrityError):
            CollaboratorModel.objects.create(
                name="Bob 2", email="bob@corp.com", department="Marketing"
            )

    def test_should_respect_meta_ordering_by_name(self) -> None:
        """Collaborators are ordered alphabetically by name."""
        collab_b = CollaboratorModel.objects.create(
            name="Zoe", email="zoe@corp.com", department="Dev"
        )
        collab_a = CollaboratorModel.objects.create(
            name="Adam", email="adam@corp.com", department="Dev"
        )
        assert list(CollaboratorModel.objects.all()) == [collab_a, collab_b]
