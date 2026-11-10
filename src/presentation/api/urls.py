"""URL routing configuration for the REST API."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

from src.presentation.api.views.collaborator_views import CollaboratorViewSet
from src.presentation.api.views.competency_views import CompetencyViewSet
from src.presentation.api.views.evaluation_views import EvaluationViewSet
from src.presentation.api.views.gap_analysis_views import GapAnalysisViewSet
from src.presentation.api.views.history_views import CompetencyHistoryViewSet
from src.presentation.api.views.path_views import CareerPathViewSet
from src.presentation.api.views.progression_views import PathProgressionViewSet

router = DefaultRouter()
router.register(r"competencies", CompetencyViewSet, basename="competency")
router.register(r"paths", CareerPathViewSet, basename="career-path")
router.register(r"collaborators", CollaboratorViewSet, basename="collaborator")
router.register(r"evaluations", EvaluationViewSet, basename="evaluation")
router.register(r"gap-analysis", GapAnalysisViewSet, basename="gap-analysis")
router.register(r"history", CompetencyHistoryViewSet, basename="competency-history")
router.register(r"progression", PathProgressionViewSet, basename="path-progression")

schema_view = get_schema_view(
    title="Competency Analytics API",
    description=(
        "Clean Architecture REST API for Competency Management, Career Paths, "
        "Evaluations, Gap Analysis, and Progression Tracking."
    ),
    version="1.0.0",
)


def swagger_ui_view(request: HttpRequest) -> HttpResponse:
    """Render interactive Swagger UI for OpenAPI documentation."""
    html = """<!DOCTYPE html>
<html>
<head>
  <title>Competency Analytics API - Swagger UI</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" />
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.onload = function() {
      SwaggerUIBundle({
        url: "/api/v1/schema/",
        dom_id: '#swagger-ui',
        presets: [SwaggerUIBundle.presets.apis],
      });
    };
  </script>
</body>
</html>"""
    return HttpResponse(html, content_type="text/html")


urlpatterns = [
    path("schema/", schema_view, name="openapi-schema"),
    path("docs/", swagger_ui_view, name="swagger-ui"),
    path("", include(router.urls)),
]
