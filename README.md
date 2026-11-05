# Personnel Competency Analysis System

A Django-based personnel competency management system built with Clean Architecture and Domain-Driven Design principles.

## Setup

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

## Dependency Injection and Composition Root

The application follows the **Dependency Inversion Principle (DIP)**. Use cases in the Application layer depend only on domain repository protocols and ports (`src/domain/repositories/`, `src/application/ports/`), not on concrete Django ORM models or database drivers.

The composition root is located at `src/presentation/dependencies/container.py`:

- **Repositories & Read Models**: Concrete implementations (`DjangoCompetencyRepository`, `DjangoPathRepository`, `DjangoCollaboratorRepository`, `DjangoEvaluationRepository`, `DjangoCompetencyHistoryReadModel`, `DjangoPathProgressionReadModel`) are wired into application use cases.
- **Singletons**: Domain services such as `GapAnalysisService` are wired as singletons across use cases.
- **Substitutability & Testing**: Views receive the container via `self.container = container or get_container()`. In tests, fake repositories or mock read models can be injected using `Container(...)` or `set_container(...)` without touching database infrastructure or HTTP views.

### Example Usage

```python
from src.presentation.dependencies import get_container, set_container, Container
from tests.unit.application.use_cases.fakes import FakeCompetencyRepository

# 1. Resolving default container in views:
container = get_container()
competency = container.get_competency_use_case.execute(competency_id)

# 2. Overriding dependencies in tests:
fake_repo = FakeCompetencyRepository()
test_container = Container(competency_repository=fake_repo)
set_container(test_container)
```
