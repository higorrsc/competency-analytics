"""Django application configuration for the competency analytics project."""

from django.apps import AppConfig


class CompetencyConfig(AppConfig):
    """Infra layer app hosting Django models mapped by domain repositories."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.django"
    label = "competency"
    verbose_name = "Competency Analytics"
