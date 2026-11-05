# Design

## Context

This is a greenfield Django project following Clean Architecture and Domain-Driven Design principles as specified in AGENTS.md. The system must maintain strict architectural boundaries where domain logic remains framework-independent while leveraging Django for infrastructure concerns (ORM, admin, authentication). All code must be fully type-annotated using Python native types (list, dict) and validated with Pyrefly.

## Goals / Non-Goals

**Goals:**

- Implement Clean Architecture with explicit layer boundaries (Domain → Application → Infrastructure → Presentation)
- Model domain using DDD aggregates with behavior-rich entities, not anemic data structures
- Keep business rules testable without Django, database, or HTTP dependencies
- Use CQRS read models (database views) for complex temporal queries
- Enforce immutability for finalized evaluations at domain and database levels
- Support comprehensive testing (unit, integration, API) with high coverage of business paths

**Non-Goals:**

- Real-time collaboration features (evaluations are individual workflows)
- External integrations with HR systems (future enhancement)
- Mobile-specific API endpoints (REST API serves all clients)
- Multi-tenancy (single organization deployment)
- Audit logging beyond evaluation immutability (future enhancement)

## Decisions

### D1: Four-Layer Clean Architecture

**Decision**: Organize code into Domain → Application → Infrastructure → Presentation layers with strict dependency rules.

**Rationale**:

- Domain layer contains pure business logic with zero framework dependencies
- Application layer orchestrates use cases without infrastructure knowledge
- Infrastructure implements abstractions defined by inner layers (repositories, database)
- Presentation adapts HTTP/Django Admin to application layer

**Structure**:

```
src/
├── domain/
│   ├── entities/          # Aggregates and entities
│   ├── value_objects/     # Immutable value types
│   ├── services/          # Domain services (gap analysis, etc.)
│   ├── repositories/      # Repository protocols (abstractions)
│   └── exceptions/        # Domain-specific exceptions
│
├── application/
│   ├── use_cases/         # Use case orchestration
│   ├── dto/               # Data transfer objects
│   └── ports/             # Application-level abstractions
│
├── infrastructure/
│   ├── django/
│   │   ├── models.py      # Django ORM models
│   │   ├── admin.py       # Django Admin configuration
│   │   ├── repositories/  # Repository implementations
│   │   └── migrations/    # Database migrations
│   └── database/
│       └── views.sql      # Database views for read models
│
└── presentation/
    ├── api/
    │   ├── views.py       # DRF viewsets
    │   ├── serializers.py # Request/response schemas
    │   └── urls.py        # URL routing
    └── dependencies.py    # Dependency injection composition root
```

**Alternatives Considered**:

- **Django-centric structure**: Rejected because it couples business logic to framework
- **Modular monolith by bounded context**: Deferred for initial version; structure supports future extraction

### D2: Domain Model with Explicit Aggregates

**Decision**: Model domain using four aggregate roots: Collaborator, Evaluation, CompetencyPath, Competency (catalog).

**Aggregate Boundaries**:

```
Collaborator (Aggregate Root)
├── CollaboratorId (Value Object)
├── name, email, department
└── enrollments: list[PathEnrollment]  (Value Objects within aggregate)
    ├── pathId (reference)
    ├── isActive: bool
    ├── targetLevel: str
    └── enrolledAt: datetime

Evaluation (Aggregate Root)
├── EvaluationId (Value Object)
├── collaboratorId (reference - not loaded, just ID)
├── evaluatorId (reference)
├── period, evaluationDate
├── status: EvaluationStatus (Enum: RASCUNHO | CONCLUÍDA | ACEITA | CONTESTADA)
└── measurements: list[CompetencyMeasurement]  (Entities within aggregate)
    ├── measurementId
    ├── competencyId (reference)
    ├── currentLevel: int (1-5)
    ├── notes, evidence

CompetencyPath (Aggregate Root)
├── PathId (Value Object)
├── name, description
└── levels: list[PathLevel]  (Entities within aggregate)
    ├── levelId
    ├── name, order
    └── requirements: list[CompetencyRequirement]  (Value Objects)
        ├── competencyId (reference)
        ├── minimumLevel: int (1-5)
        └── weight: RequirementWeight (Enum: CORE | IMPORTANT | DESIRABLE)

Competency (Aggregate Root / Catalog)
├── CompetencyId (Value Object)
├── name, description
├── categoryId, groupId (references to hierarchy)
└── levelDescriptions: dict[int, str]  (1-5 mapped to descriptions)
```

**Rationale**:

- Each aggregate has clear consistency boundary
- Evaluation measurements cannot exist without parent evaluation (consistency)
- Path requirements cannot exist without parent level (consistency)
- Collaborator enrollments enforce "only one active path" rule within aggregate
- References between aggregates use IDs only (loose coupling)

**Alternatives Considered**:

- **Anemic domain model with service layer**: Rejected per AGENTS.md guidance - prefer behavior-rich entities
- **Larger aggregates**: PathLevel as separate aggregate - rejected, tightly coupled lifecycle with Path

### D3: Repository Abstractions with Protocol Types

**Decision**: Define repositories as Protocol types in domain/application layer, implement in infrastructure.

**Example**:

```python
# domain/repositories/evaluation_repository.py
from typing import Protocol
from domain.entities.evaluation import Evaluation, EvaluationId
from domain.value_objects.collaborator_id import CollaboratorId


class EvaluationRepository(Protocol):
    """Repository abstraction for Evaluation aggregate."""

    def save(self, evaluation: Evaluation) -> None:
        """Persist evaluation aggregate."""
        ...

    def get_by_id(self, evaluation_id: EvaluationId) -> Evaluation | None:
        """Retrieve evaluation by ID."""
        ...

    def find_latest_finalized_for_collaborator(
        self, collaborator_id: CollaboratorId
    ) -> Evaluation | None:
        """Get most recent ACEITA or CONTESTADA evaluation."""
        ...


# infrastructure/django/repositories/django_evaluation_repository.py
class DjangoEvaluationRepository:
    """Django ORM implementation of EvaluationRepository."""

    def save(self, evaluation: Evaluation) -> None:
        # Map domain entity to Django model and save
        ...
```

**Rationale**:

- Domain/application never imports Django or SQLAlchemy
- Tests use fake repositories (fast, no database)
- Can swap persistence implementation without changing domain

**Alternatives Considered**:

- **ABC base classes**: Protocol is more Pythonic and doesn't require inheritance
- **Direct Django model usage in use cases**: Violates Clean Architecture

### D4: CQRS Read Models with Database Views

**Decision**: Implement temporal queries and aggregations using PostgreSQL views accessed through read model repositories.

**Read Models**:

```sql
-- infrastructure/database/views/collaborator_competency_history.sql
CREATE VIEW collaborator_competency_history AS
SELECT 
    c.id as collaborator_id,
    comp.id as competency_id,
    comp.name as competency_name,
    e.evaluation_date,
    e.period,
    cm.current_level,
    LAG(cm.current_level) OVER (
        PARTITION BY c.id, comp.id 
        ORDER BY e.evaluation_date
    ) as previous_level,
    cm.current_level - LAG(cm.current_level) OVER (
        PARTITION BY c.id, comp.id 
        ORDER BY e.evaluation_date
    ) as level_change,
    e.status
FROM collaborators c
JOIN evaluations e ON e.collaborator_id = c.id
JOIN competency_measurements cm ON cm.evaluation_id = e.id
JOIN competencies comp ON comp.id = cm.competency_id
WHERE e.status IN ('ACEITA', 'CONTESTADA');

-- infrastructure/database/views/path_progression_summary.sql
CREATE VIEW path_progression_summary AS
SELECT
    c.id as collaborator_id,
    pe.path_id,
    pe.target_level,
    COUNT(cr.id) as total_requirements,
    COUNT(CASE 
        WHEN latest_cm.current_level >= cr.minimum_level 
        THEN 1 
    END) as requirements_met,
    ROUND(
        100.0 * COUNT(CASE 
            WHEN latest_cm.current_level >= cr.minimum_level 
            THEN 1 
        END) / COUNT(cr.id),
        2
    ) as completion_percentage
FROM collaborators c
JOIN path_enrollments pe ON pe.collaborator_id = c.id AND pe.is_active = true
JOIN path_levels pl ON pl.path_id = pe.path_id AND pl.name = pe.target_level
JOIN competency_requirements cr ON cr.path_level_id = pl.id
LEFT JOIN LATERAL (
    SELECT DISTINCT ON (e.collaborator_id, cm.competency_id)
        cm.competency_id,
        cm.current_level
    FROM evaluations e
    JOIN competency_measurements cm ON cm.evaluation_id = e.id
    WHERE e.collaborator_id = c.id
      AND e.status IN ('ACEITA', 'CONTESTADA')
    ORDER BY e.collaborator_id, cm.competency_id, e.evaluation_date DESC
) latest_cm ON latest_cm.competency_id = cr.competency_id
GROUP BY c.id, pe.path_id, pe.target_level;
```

**Access Pattern**:

```python
# application/ports/read_models.py
class CompetencyHistoryReadModel(Protocol):
    """Read model for temporal competency queries."""
    
    def get_history(
        self,
        collaborator_id: CollaboratorId,
        competency_id: CompetencyId | None = None,
        start_date: date | None = None,
        end_date: date | None = None
    ) -> list[CompetencyHistoryEntry]:
        """Query competency evolution over time."""
        ...

# infrastructure/django/read_models/django_competency_history_read_model.py
class DjangoCompetencyHistoryReadModel:
    """Queries collaborator_competency_history view."""
    
    def get_history(...):
        # Query the database view with filters
        return [CompetencyHistoryEntry(...) for row in queryset]
```

**Rationale**:

- Complex temporal queries are significantly faster using window functions
- Separates read concerns from write/command aggregates (CQRS)
- Read models can be optimized independently without affecting domain
- Views are created via Django migrations, versioned with schema

**Alternatives Considered**:

- **Load all evaluations into memory**: Doesn't scale with evaluation history
- **N+1 queries in application layer**: Performs poorly
- **Denormalized tables**: Views are simpler and auto-update

### D5: Evaluation Immutability Enforcement

**Decision**: Enforce evaluation immutability at both domain entity level and database constraint level once finalized.

**Domain Enforcement**:

```python
# domain/entities/evaluation.py
class Evaluation:
    """Evaluation aggregate root."""
    
    def add_measurement(self, measurement: CompetencyMeasurement) -> None:
        """Add measurement only in RASCUNHO state."""
        if not self.status.is_draft():
            raise EvaluationImmutableError("Cannot modify finalized evaluation")
        self._measurements.append(measurement)
    
    def accept(self, response_notes: str | None = None) -> None:
        """Employee accepts evaluation, making it immutable."""
        if self.status != EvaluationStatus.CONCLUIDA:
            raise InvalidStatusTransitionError(...)
        self._status = EvaluationStatus.ACEITA
        self._response_date = datetime.now()
        self._response_notes = response_notes
```

**Database Enforcement**:

```python
# infrastructure/django/models.py
class EvaluationModel(models.Model):
    """Django model with database-level immutability checks."""
    
    def save(self, *args, **kwargs):
        if self.pk:  # Existing record
            old = EvaluationModel.objects.get(pk=self.pk)
            if old.status in ['ACEITA', 'CONTESTADA']:
                raise IntegrityError("Cannot modify finalized evaluation")
        super().save(*args, **kwargs)

# Migration with check constraint
ALTER TABLE evaluations ADD CONSTRAINT evaluation_immutable_check
CHECK (
    status NOT IN ('ACEITA', 'CONTESTADA') OR
    (created_at IS NOT NULL AND updated_at = created_at)
);
```

**Rationale**:

- Domain-level enforcement prevents business logic violations
- Database-level enforcement prevents direct SQL modifications
- Immutability is critical for audit compliance and historical accuracy

**Alternatives Considered**:

- **Event sourcing**: Overkill for initial version, but immutability paves the way
- **Soft delete only**: Doesn't prevent updates to finalized records

### D6: Domain Service for Gap Analysis

**Decision**: Implement competency gap calculation as pure domain service with no infrastructure dependencies.

**Implementation**:

```python
# domain/services/gap_analysis_service.py
class GapAnalysisService:
    """Pure domain service for calculating competency gaps."""

    def calculate_gaps(
        self, evaluation: Evaluation, target_level: PathLevel
    ) -> list[CompetencyGap]:
        """
        Calculate gaps between evaluation and path level requirements.

        Pure function - no database queries, no external calls.
        """
        gaps: list[CompetencyGap] = []

        for requirement in target_level.requirements:
            measurement = evaluation.find_measurement(requirement.competency_id)

            if measurement is None:
                gap_size = requirement.minimum_level
                current_level = 0
            else:
                current_level = measurement.current_level
                gap_size = max(0, requirement.minimum_level - current_level)

            gaps.append(
                CompetencyGap(
                    competency_id=requirement.competency_id,
                    current_level=current_level,
                    required_level=requirement.minimum_level,
                    gap=gap_size,
                    weight=requirement.weight,
                )
            )

        # Sort by weight (CORE first), then gap size
        return self._sort_by_priority(gaps)
```

**Rationale**:

- Testable without database or mocks (pure logic)
- Accepts domain entities as input, returns domain value objects
- Can be executed in-memory with test data
- Follows AGENTS.md mandate: domain services for cross-aggregate operations

**Alternatives Considered**:

- **Repository-based service**: Would couple business logic to infrastructure
- **Database stored procedure**: Not portable, not testable as domain logic

### D7: Technology Stack Choices

**Decision**: Use UV for dependencies, Ruff for linting, Pyrefly for type checking, Pytest for testing.

| Concern | Technology | Rationale |
| --------- | ----------- | ----------- |
| Dependency Management | UV | Fast, modern Python package installer per AGENTS.md |
| Linting & Formatting | Ruff | Rust-based, extremely fast, replaces multiple tools |
| Type Checking | Pyrefly | Required by AGENTS.md for static analysis |
| Testing | Pytest | Industry standard, excellent fixtures and parametrization |
| Web Framework | Django 5.1+ | Admin interface, ORM, auth per project requirements |
| API Framework | Django REST Framework | Standard REST API on top of Django |
| Database | PostgreSQL 16+ | Window functions, JSON support, views, check constraints |
| Python Version | 3.12+ | Native type syntax (list, dict), pattern matching |

**Type Annotation Strategy**:

- Use Python native types: `list[T]`, `dict[K, V]`, not `List[T]`, `Dict[K, V]`
- Use `Protocol` for structural typing (repositories, read models)
- Use `|` for unions: `Evaluation | None`, not `Optional[Evaluation]`
- Comprehensive docstrings on all classes (including dataclass/Pydantic) and methods
- No `Any` types unless absolutely necessary with documented justification

**Alternatives Considered**:

- **Poetry**: UV is faster and simpler
- **mypy**: Pyrefly specified in AGENTS.md
- **FastAPI instead of Django**: Rejected - need Django Admin capabilities

### D8: Testing Strategy

**Decision**: Implement comprehensive test coverage with pyramid structure emphasizing unit tests.

**Test Organization**:

```
tests/
├── unit/
│   ├── domain/
│   │   ├── test_evaluation.py          # Entity behavior
│   │   ├── test_collaborator.py        # Active path enforcement
│   │   ├── test_gap_analysis_service.py # Pure logic
│   │   └── test_competency.py
│   └── application/
│       ├── test_create_evaluation_use_case.py
│       └── test_calculate_gaps_use_case.py
│
├── integration/
│   ├── test_django_repositories.py      # Database integration
│   └── test_read_models.py              # View queries
│
└── api/
    ├── test_evaluation_endpoints.py     # REST API contracts
    └── test_gap_analysis_endpoints.py
```

**Coverage Targets**:

- Domain layer: 95%+ (all business rules)
- Application layer: 85%+
- Infrastructure: 70%+ (happy paths + key error cases)
- API: 80%+ (all endpoints, status codes, error responses)

**Test Doubles Preference** (per AGENTS.md):

1. **Fake** repositories for use case tests (in-memory, no database)
2. **Stubs** for read models when testing presentation
3. **Mocks** only when interaction verification is required

**Rationale**:

- Fast unit tests enable TDD workflow
- Domain tests run without Django/database setup
- Integration tests verify infrastructure contracts
- API tests verify public contracts

**Alternatives Considered**:

- **Only integration tests**: Too slow for TDD
- **Heavy mocking**: Makes tests brittle and implementation-aware

## Risks / Trade-offs

### R1: Learning Curve for Clean Architecture

**Risk**: Developers unfamiliar with DDD/Clean Architecture may find structure complex.

**Mitigation**:

- Comprehensive documentation in AGENTS.md provides guidelines
- Clear examples in initial implementation serve as templates
- Separation of concerns simplifies reasoning once understood
- Each layer has clear responsibility

### R2: Django ORM Mapping Complexity

**Risk**: Mapping between Django models and domain entities adds translation layer overhead.

**Trade-off**: Accepted for architectural purity.

**Mitigation**:

- Repository implementations centralize mapping logic
- Use dataclass/Pydantic for DTOs to simplify serialization
- Write integration tests to catch mapping bugs early

### R3: Database View Maintenance

**Risk**: Complex views require careful migration management and can break with schema changes.

**Mitigation**:

- Views defined in Django migrations with version control
- Integration tests verify view queries return expected shape
- Document view purpose and dependencies in migration comments
- Use `IF EXISTS` for safe migrations

### R4: Evaluation Immutability vs Corrections

**Risk**: Legitimate corrections to finalized evaluations are blocked by immutability.

**Trade-off**: Historical integrity prioritized over correction capability.

**Mitigation**:

- Documented process: create new evaluation for corrections
- Consider future enhancement: amendment/correction workflow
- Database audit log (future) can track why new evaluation created

### R5: Type Checking Overhead

**Risk**: Full type annotations and Pyrefly checking may slow development initially.

**Trade-off**: Accepted for long-term maintainability and bug prevention.

**Mitigation**:

- Type errors caught before runtime reduces debugging time
- IDE autocomplete improves development speed
- Pyrefly integrated into CI prevents type drift

### R6: Gap Analysis Performance with Large Paths

**Risk**: Gap calculation in-memory may be slow for paths with 100+ requirements.

**Trade-off**: Domain purity prioritized over optimization for edge cases.

**Mitigation**:

- Initial implementation handles realistic path sizes (10-30 requirements)
- Profiling before optimization (per AGENTS.md)
- Future optimization: repository can pre-filter measurements by required competencies
- Gap analysis is infrequent operation (not every request)

## Migration Plan

N/A - Greenfield project, no migration required.

## Open Questions

None - all design decisions needed for implementation are resolved.
