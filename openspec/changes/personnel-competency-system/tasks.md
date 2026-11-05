# Tasks

## 1. Project Setup and Structure

- [x] 1.1 Initialize Django project with UV dependency management and verify `uv run manage.py --version` succeeds
- [x] 1.2 Add project dependencies (Django 5.1+, DRF, psycopg, pytest, pytest-django, ruff, pyrefly) to pyproject.toml and verify `uv sync` completes
- [x] 1.3 Create Clean Architecture directory structure (domain/, application/, infrastructure/, presentation/) and verify all __init__.py files exist
- [x] 1.4 Configure Django settings with PostgreSQL database connection and verify migrations can be created
- [x] 1.5 Setup pytest configuration (pytest.ini, conftest.py) with Django settings and verify `uv run pytest --collect-only` succeeds
- [x] 1.6 Configure Ruff (pyproject.toml) and Pyrefly and verify `uv run ruff check .` and `uv run pyrefly check` run without errors on empty structure
- [x] 1.7 Create .env.example with required environment variables and verify documentation is clear

## 2. Domain Layer - Value Objects and Enums

- [x] 2.1 Implement EvaluationStatus enum (RASCUNHO, CONCLUÍDA, ACEITA, CONTESTADA) and verify unit test covers all states and transitions
- [x] 2.2 Implement RequirementWeight enum (CORE, IMPORTANT, DESIRABLE) and verify unit test covers ordering and comparison
- [x] 2.3 Implement CollaboratorId value object with validation and verify unit test covers creation and equality
- [x] 2.4 Implement EvaluationId value object with validation and verify unit test covers creation and equality
- [x] 2.5 Implement CompetencyId value object with validation and verify unit test covers creation and equality
- [x] 2.6 Implement PathId value object with validation and verify unit test covers creation and equality
- [x] 2.7 Add docstrings to all value objects/enums and verify Pyrefly type check passes

## 3. Domain Layer - Competency Catalog Aggregate

- [x] 3.1 Implement Competency entity with hierarchy (categoryId, groupId), level descriptions (dict[int, str]), and verify unit test covers creation
- [x] 3.2 Add validation to Competency requiring all 5 level descriptions and verify test covers missing levels rejection
- [x] 3.3 Implement CompetencyRepository protocol with save, get_by_id, find_by_hierarchy methods and verify protocol structure with Pyrefly
- [x] 3.4 Add domain exception CompetencyReferencedError for deletion prevention and verify unit test covers exception creation
- [x] 3.5 Document Competency aggregate in domain/entities/competency.py with comprehensive docstrings

## 4. Domain Layer - CompetencyPath Aggregate

- [x] 4.1 Implement CompetencyRequirement value object (competencyId, minimumLevel, weight) and verify unit test covers creation and validation
- [x] 4.2 Implement PathLevel entity (levelId, name, order, requirements list) and verify unit test covers requirement management
- [x] 4.3 Implement CompetencyPath aggregate root with levels list and verify unit test covers level ordering validation
- [x] 4.4 Add business rule to PathLevel preventing duplicate competency requirements and verify unit test covers rejection
- [x] 4.5 Add business rule to CompetencyPath enforcing sequential level ordering and verify unit test covers non-sequential rejection
- [x] 4.6 Implement PathRepository protocol with save, get_by_id, find_all methods and verify protocol structure
- [x] 4.7 Document CompetencyPath aggregate with docstrings covering business rules

## 5. Domain Layer - Collaborator Aggregate

- [x] 5.1 Implement PathEnrollment value object (pathId, isActive, targetLevel, enrolledAt) and verify unit test covers creation
- [x] 5.2 Implement Collaborator aggregate root with enrollments list and verify unit test covers enrollment addition
- [x] 5.3 Add business rule enforcing single active path with set_active_path method and verify unit test covers automatic deactivation
- [x] 5.4 Add validation preventing duplicate path enrollments and verify unit test covers rejection
- [x] 5.5 Implement update_target_level method with validation and verify unit test covers level existence check
- [x] 5.6 Implement CollaboratorRepository protocol with save, get_by_id, find_by_path methods and verify protocol structure
- [x] 5.7 Document Collaborator aggregate with docstrings covering single active path invariant

## 6. Domain Layer - Evaluation Aggregate

- [x] 6.1 Implement CompetencyMeasurement entity (measurementId, competencyId, currentLevel, notes, evidence) and verify unit test covers creation and level validation
- [x] 6.2 Implement Evaluation aggregate root with measurements list, status, dates and verify unit test covers creation in RASCUNHO state
- [x] 6.3 Add add_measurement method enforcing draft-only modification and verify unit test covers immutability after completion
- [x] 6.4 Add submit method transitioning RASCUNHO → CONCLUÍDA with validation and verify unit test covers empty measurements rejection
- [x] 6.5 Add accept method transitioning CONCLUÍDA → ACEITA with response notes and verify unit test covers status validation
- [x] 6.6 Add contest method transitioning CONCLUÍDA → CONTESTADA requiring notes and verify unit test covers missing notes rejection
- [x] 6.7 Add business rule preventing any modification when status is ACEITA/CONTESTADA and verify unit test covers all modification attempts blocked
- [x] 6.8 Implement EvaluationRepository protocol with save, get_by_id, find_latest_finalized_for_collaborator methods and verify protocol structure
- [x] 6.9 Add domain exceptions (EvaluationImmutableError, InvalidStatusTransitionError) and verify unit tests cover creation
- [x] 6.10 Document Evaluation aggregate with comprehensive docstrings covering lifecycle and immutability

## 7. Domain Layer - Gap Analysis Domain Service

- [x] 7.1 Implement CompetencyGap value object (competencyId, currentLevel, requiredLevel, gap, weight) and verify unit test covers creation
- [x] 7.2 Implement GapAnalysisService.calculate_gaps accepting Evaluation and PathLevel entities and verify unit test with in-memory entities calculates correct gaps
- [x] 7.3 Add gap sorting logic (CORE first, then IMPORTANT, then DESIRABLE, secondary by gap size) and verify unit test covers ordering
- [x] 7.4 Handle unmeasured competencies treating them as level 0 and verify unit test covers full gap for missing measurements
- [x] 7.5 Implement progression eligibility check based on CORE requirements and verify unit test covers eligible/not eligible scenarios
- [x] 7.6 Add generate_recommendation method producing textual guidance and verify unit test covers different gap sizes and weights
- [x] 7.7 Verify service has zero infrastructure dependencies (no imports from infrastructure/presentation) and run Pyrefly to confirm
- [x] 7.8 Document GapAnalysisService with docstrings explaining pure domain logic approach

## 8. Application Layer - DTOs and Ports

- [x] 8.1 Create Pydantic DTOs for Competency (CompetencyCreateDTO, CompetencyResponseDTO) and verify validation with unit tests
- [x] 8.2 Create Pydantic DTOs for CompetencyPath (PathCreateDTO, PathResponseDTO, LevelCreateDTO) and verify validation
- [x] 8.3 Create Pydantic DTOs for Collaborator (CollaboratorCreateDTO, EnrollmentCreateDTO, CollaboratorResponseDTO) and verify validation
- [x] 8.4 Create Pydantic DTOs for Evaluation (EvaluationCreateDTO, MeasurementCreateDTO, EvaluationResponseDTO) and verify validation
- [x] 8.5 Create Pydantic DTOs for gap analysis (GapAnalysisRequestDTO, GapAnalysisResponseDTO) and verify validation
- [x] 8.6 Define CompetencyHistoryReadModel protocol with get_history method and verify protocol structure
- [x] 8.7 Define PathProgressionReadModel protocol with get_progression_summary method and verify protocol structure
- [x] 8.8 Add comprehensive docstrings to all DTOs and protocols

## 9. Application Layer - Use Cases

- [x] 9.1 Implement CreateCompetencyUseCase with repository injection and verify unit test with fake repository covers happy path
- [x] 9.2 Implement CreateCareerPathUseCase and verify unit test covers level ordering validation
- [x] 9.3 Implement EnrollCollaboratorInPathUseCase enforcing single active path and verify unit test with fake repository
- [x] 9.4 Implement CreateEvaluationUseCase creating draft evaluation and verify unit test covers collaborator validation
- [x] 9.5 Implement AddMeasurementToEvaluationUseCase validating draft status and verify unit test covers immutability enforcement
- [x] 9.6 Implement SubmitEvaluationUseCase transitioning to CONCLUÍDA and verify unit test covers measurement requirement
- [x] 9.7 Implement AcceptEvaluationUseCase (collaborator action) and verify unit test covers status transition
- [x] 9.8 Implement ContestEvaluationUseCase requiring notes and verify unit test covers notes validation
- [x] 9.9 Implement CalculateCompetencyGapsUseCase coordinating repositories and domain service and verify unit test with fakes
- [x] 9.10 Add error handling translating domain exceptions to application-level errors and verify unit tests cover error scenarios
- [x] 9.11 Document all use cases with docstrings explaining orchestration flow

## 10. Infrastructure - Django Models

- [x] 10.1 Create Django models for competency hierarchy (CategoryModel, CompetencyGroupModel, CompetencyModel) and verify migrations generate
- [x] 10.2 Create CompetencyPathModel and PathLevelModel with ordering and verify migrations
- [x] 10.3 Create CompetencyRequirementModel linking PathLevel to Competency and verify migrations
- [x] 10.4 Create CollaboratorModel with basic fields and verify migrations
- [x] 10.5 Create PathEnrollmentModel with unique_together constraint and verify migrations
- [x] 10.6 Create EvaluationModel with status field and dates and verify migrations
- [x] 10.7 Create CompetencyMeasurementModel linking Evaluation to Competency and verify migrations
- [x] 10.8 Add database check constraint preventing modification of finalized evaluations and verify migration
- [x] 10.9 Add model-level save override enforcing immutability in EvaluationModel and verify integration test with database
- [x] 10.10 Add __str__ methods and Meta ordering to all models and verify Django admin display
- [x] 10.11 Run migrations on test database and verify schema created successfully

## 11. Infrastructure - Repository Implementations

- [x] 11.1 Implement DjangoCompetencyRepository mapping domain Competency to/from CompetencyModel and verify integration test with database
- [x] 11.2 Add reference check preventing competency deletion when used in paths or evaluations and verify integration test covers rejection
- [x] 11.3 Implement DjangoPathRepository mapping CompetencyPath aggregate and verify integration test covers nested levels and requirements
- [x] 11.4 Implement DjangoCollaboratorRepository mapping Collaborator with enrollments and verify integration test covers active path queries
- [x] 11.5 Implement DjangoEvaluationRepository mapping Evaluation with measurements and verify integration test covers measurement persistence
- [x] 11.6 Add find_latest_finalized_for_collaborator query filtering ACEITA/CONTESTADA status and verify integration test with multiple evaluations
- [x] 11.7 Verify all repository methods properly map between domain entities and Django models without leaking ORM into domain
- [x] 11.8 Add docstrings to all repository implementations explaining mapping strategy

## 12. Infrastructure - Database Views for Read Models

- [x] 12.1 Create SQL migration for collaborator_competency_history view with window functions and verify migration applies
- [x] 12.2 Create SQL migration for path_progression_summary view with aggregations and verify migration applies
- [x] 12.3 Implement DjangoCompetencyHistoryReadModel querying view and verify integration test returns correct historical data
- [x] 12.4 Implement DjangoPathProgressionReadModel querying view and verify integration test calculates correct completion percentage
- [x] 12.5 Add filtering by date range to history read model and verify integration test covers date filtering
- [x] 12.6 Verify views include only finalized evaluations (ACEITA/CONTESTADA) and integration test confirms drafts excluded
- [x] 12.7 Document views in migration comments explaining purpose and dependencies

## 13. Presentation - Django Admin

- [x] 13.1 Register Category, CompetencyGroup, Competency models in admin with hierarchical display and verify admin interface accessible
- [x] 13.2 Register CompetencyPath and PathLevel with inline level editing and verify admin interface allows level management
- [x] 13.3 Register Collaborator with inline enrollment editing and verify admin interface shows active path
- [x] 13.4 Register Evaluation with inline measurement editing, read-only fields for finalized, and verify admin enforces immutability
- [x] 13.5 Add custom admin actions for path enrollment activation and verify action correctly deactivates others
- [x] 13.6 Add list filters for evaluation status, collaborator department and verify filtering works in admin
- [x] 13.7 Customize admin display with list_display, search_fields for all models and verify searchability

## 14. Presentation - REST API Endpoints

- [x] 14.1 Implement CompetencyViewSet (CRUD) with DRF and verify API test covers create, list, retrieve
- [x] 14.2 Implement CareerPathViewSet with nested level/requirement serialization and verify API test covers complete structure
- [x] 14.3 Implement CollaboratorViewSet with enrollment management endpoints and verify API test covers enrollment creation
- [x] 14.4 Add custom action for activating path enrollment and verify API test covers activation and automatic deactivation
- [x] 14.5 Implement EvaluationViewSet with status transition endpoints (submit, accept, contest) and verify API tests cover all transitions
- [x] 14.6 Add nested route for adding measurements to evaluation and verify API test covers draft-only modification
- [x] 14.7 Implement read-only endpoint for competency gap analysis and verify API test returns correct gap calculation
- [x] 14.8 Implement read-only endpoint for competency history and verify API test returns temporal data
- [x] 14.9 Add error handling returning appropriate HTTP status codes (400, 404, 409) and verify API tests cover error responses
- [x] 14.10 Add API documentation with OpenAPI schema and verify swagger UI accessible
- [x] 14.11 Configure URL routing for all endpoints and verify `uv run manage.py show_urls` displays all routes

## 15. Dependency Injection and Composition Root

- [x] 15.1 Create dependency injection container in presentation/dependencies.py wiring use cases to repositories and verify structure
- [x] 15.2 Wire GapAnalysisService as singleton and verify use case receives same instance
- [x] 15.3 Configure DRF views to inject use cases via dependencies and verify API endpoints use correct use case instances
- [x] 15.4 Verify no direct repository instantiation in use cases and run Pyrefly to confirm proper injection
- [x] 15.5 Document dependency injection approach in README with examples

## 16. Integration Testing

- [x] 16.1 Create end-to-end test: create competency catalog → create path → enroll collaborator → create evaluation → calculate gaps, and verify complete workflow succeeds
- [x] 16.2 Create integration test for evaluation lifecycle: draft → add measurements → submit → accept, and verify immutability enforced
- [x] 16.3 Create integration test for contested evaluation: draft → submit → contest, and verify contestation notes required
- [x] 16.4 Create integration test for active path switching: enroll in path A → activate → enroll in path B → activate, and verify only B active
- [x] 16.5 Create integration test for gap analysis with missing measurements: evaluation with partial measurements → calculate gaps, and verify unmeasured treated as level 0
- [x] 16.6 Create integration test for temporal queries: multiple evaluations over time → query history, and verify chronological ordering with level changes
- [x] 16.7 Create integration test preventing competency deletion: competency used in path → attempt delete, and verify rejection with reference error
- [x] 16.8 Verify all integration tests use real database (not fakes) and complete successfully

## 17. Documentation and Finalization

- [x] 17.1 Create README.md with project overview, setup instructions, and architecture diagram
- [x] 17.2 Document environment variables in .env.example with descriptions
- [x] 17.3 Create development guide explaining how to run tests, linting, type checking
- [x] 17.4 Document API endpoints with example requests/responses
- [x] 17.5 Create architecture documentation explaining Clean Architecture layers and boundaries
- [x] 17.6 Add docstrings validation to CI checks and verify all public APIs documented
- [x] 17.7 Run complete test suite and verify >85% coverage achieved
- [x] 17.8 Run `uv run ruff format .` and verify code formatted
- [x] 17.9 Run `uv run ruff check .` and verify no linting errors
- [x] 17.10 Run `uv run pyrefly check` and verify no type errors
- [x] 17.11 Create Git hooks for pre-commit checks (format, lint, type check, tests) and verify hooks execute

## 18. System Verification

- [x] 18.1 Start development server and verify all endpoints accessible
- [x] 18.2 Access Django admin and verify all models manageable
- [x] 18.3 Create sample data via admin and verify data persists correctly
- [ ] 18.4 Execute complete user workflow via API and verify responses match specs
- [ ] 18.5 Verify database views return correct data matching manual queries
- [ ] 18.6 Run performance test on gap analysis with large path (30+ requirements) and verify acceptable response time
- [ ] 18.7 Verify application startup, API calls, and shutdown produce no errors in logs
- [ ] 18.8 Run full test suite with coverage report and verify all specs have corresponding tests

## Workflow follow-up

- Review the implementation against AGENTS.md principles ensuring domain independence from Django
- Verify Clean Architecture boundaries are maintained with layer dependency checks
- Archive the change after all tasks are complete and verified
