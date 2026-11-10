"""Collaborator and PathEnrollment Django Admin configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin, messages
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest

from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.path_enrollment import PathEnrollmentModel

if TYPE_CHECKING:
    _EnrollmentInlineBase = admin.TabularInline[PathEnrollmentModel, CollaboratorModel]
    _CollabAdminBase = admin.ModelAdmin[CollaboratorModel]
    _EnrollmentAdminBase = admin.ModelAdmin[PathEnrollmentModel]
else:
    _EnrollmentInlineBase = admin.TabularInline
    _CollabAdminBase = admin.ModelAdmin
    _EnrollmentAdminBase = admin.ModelAdmin


@admin.action(description="Activate selected enrollment (deactivates other paths)")
def activate_enrollment_action(
    modeladmin: admin.ModelAdmin[PathEnrollmentModel],
    request: HttpRequest,
    queryset: QuerySet[PathEnrollmentModel],
) -> None:
    """
    Activate selected enrollments, ensuring single active path per collaborator.

    Deactivates any other active enrollments for the same collaborator so the
    domain invariant (at most one active enrollment per collaborator) is preserved.
    """
    activated_count = 0
    with transaction.atomic():
        for enrollment in queryset:
            PathEnrollmentModel.objects.filter(
                collaborator_id=enrollment.collaborator_id
            ).exclude(id=enrollment.id).update(is_active=False)
            enrollment.is_active = True
            enrollment.save(update_fields=["is_active"])
            activated_count += 1

    modeladmin.message_user(
        request,
        f"Successfully activated {activated_count} enrollment(s).",
        messages.SUCCESS,
    )


class PathEnrollmentInline(_EnrollmentInlineBase):
    """Inline editing for path enrollments directly within Collaborator."""

    model = PathEnrollmentModel
    extra = 1
    fields = ("path", "target_level", "is_active", "enrolled_at")
    ordering = ("-enrolled_at",)


class CollaboratorAdmin(_CollabAdminBase):
    """Admin configuration for CollaboratorModel with inline enrollments."""

    inlines = (PathEnrollmentInline,)
    list_display = ("name", "email", "department", "active_path_display")
    list_filter = ("department", "enrollments__path", "enrollments__is_active")
    search_fields = ("name", "email", "department")
    ordering = ("name",)

    @admin.display(description="Active Career Path")
    def active_path_display(self, obj: CollaboratorModel) -> str:
        """Display the active career path and target level for the collaborator."""
        active = (
            PathEnrollmentModel.objects.filter(collaborator_id=obj.id, is_active=True)
            .select_related("path")
            .first()
        )
        if active is None:
            return "No Active Path"
        return f"{active.path.name} ({active.target_level})"


class PathEnrollmentAdmin(_EnrollmentAdminBase):
    """Admin configuration for PathEnrollmentModel with custom activation action."""

    list_display = (
        "collaborator",
        "path",
        "target_level",
        "is_active",
        "enrolled_at",
    )
    list_filter = ("is_active", "path", "collaborator__department")
    search_fields = (
        "collaborator__name",
        "collaborator__email",
        "path__name",
        "target_level",
    )
    ordering = ("-enrolled_at",)
    actions = (activate_enrollment_action,)
