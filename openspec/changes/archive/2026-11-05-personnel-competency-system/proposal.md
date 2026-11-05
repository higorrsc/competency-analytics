# Proposal

## Why

Organizations need to track employee competency development over time and guide career progression along defined paths. Currently, there is no structured system to conduct formal competency evaluations, calculate skill gaps against career requirements, or visualize competency growth over assessment periods. This system provides the foundation for performance management and career development.

## What Changes

- Create a complete personnel competency management system from scratch (greenfield)
- Implement hierarchical competency catalog with 3-level structure (Category → Group → Competency)
- Enable formal evaluation workflows with immutable historical records
- Support multiple career paths with level-based competency requirements
- Calculate competency gaps between current state and target career levels
- Track competency evolution over time through temporal queries
- Use Django for admin interfaces, ORM, and authentication while keeping business rules in domain layer
- Follow Clean Architecture with strong separation between domain, application, infrastructure, and presentation layers
- Use Python native types (list, dict) with full type annotations checked by Pyrefly
- Manage dependencies with UV, lint with Ruff, test with Pytest

## Capabilities

### New Capabilities

- `competency-catalog`: Manage hierarchical competency catalog with categories, groups, and individual competencies. Each competency defines 5 proficiency levels with descriptions. Supports creating, updating, and organizing competencies with validation that prevents deletion when referenced by paths or evaluations.

- `career-paths`: Manage career progression paths with multiple levels (Junior, Mid, Senior, etc.). Each level defines competency requirements with minimum proficiency levels and weights (core, important, desirable). Supports defining, modifying, and querying career progression structures.

- `collaborator-management`: Manage employee records and their enrollments in career paths. Enforces business rule that only one path can be active at a time while allowing historical tracking of multiple path enrollments.

- `evaluation-management`: Conduct formal competency evaluations with structured workflow (RASCUNHO → CONCLUÍDA → ACEITA/CONTESTADA). Once finalized, evaluations become immutable historical records. Supports measuring competencies against the 1-5 scale with notes and evidence, and employee acceptance/contestation of results.

- `competency-gap-analysis`: Calculate gaps between current competency levels (from latest evaluation) and required levels (from target career path level). Implemented as pure domain service with no infrastructure dependencies. Produces prioritized development recommendations based on requirement weights.

- `competency-progress-tracking`: Query and visualize competency evolution over time through database views and read models. Supports temporal comparisons, trend analysis, and career progression monitoring through CQRS-style read models optimized for reporting.

### Modified Capabilities

<!-- No existing capabilities to modify - this is a greenfield project -->

## Impact

**New Components:**

- Domain layer with aggregates (Collaborator, Evaluation, CompetencyPath, Competency), value objects, and domain services
- Application layer with use cases and DTOs
- Infrastructure layer with Django ORM models, repositories, and database views
- Presentation layer with Django Admin interfaces and REST API
- Comprehensive test suite covering domain, application, integration, and API layers

**Technology Stack:**

- Python 3.12+ with native typing
- Django + Django REST Framework
- PostgreSQL with database views for temporal queries
- UV for dependency management
- Ruff for linting and formatting
- Pyrefly for static type checking
- Pytest for testing

**Architectural Decisions:**

- Clean Architecture with strict layer boundaries
- Domain-Driven Design with explicit aggregates and domain services
- Django as infrastructure adapter, not domain location
- CQRS read models (database views) for complex temporal queries
- Immutable evaluation history for audit compliance
- Type-safe codebase with comprehensive docstrings

**Breaking Changes:**
None - this is a new system.
