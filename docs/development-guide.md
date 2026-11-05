# Development Guide

This guide details local development workflows, testing strategies, static analysis requirements, and contribution guidelines for the **Personnel Competency Analysis System**.

All contributors must adhere to the engineering standards specified in this guide and in [`AGENTS.md`](../AGENTS.md).

---

## Table of Contents

- [Development Workflow](#development-workflow)
- [Environment Setup](#environment-setup)
- [Testing Strategy](#testing-strategy)
  - [Test Hierarchy](#test-hierarchy)
  - [Executing Tests](#executing-tests)
  - [Test Doubles & Fakes](#test-doubles--fakes)
  - [Test Naming Conventions](#test-naming-conventions)
- [Code Formatting & Linting](#code-formatting--linting)
- [Static Type Checking](#static-type-checking)
- [Pre-Commit Quality Gate](#pre-commit-quality-gate)
- [Git Flow & Commit Standards](#git-flow--commit-standards)

---

## Development Workflow

Development follows a strict test-first / spec-driven lifecycle:

```text
Specification / Task
        ↓
Write / Update Tests (Failing)
        ↓
Implement Domain Logic
        ↓
Implement Application Use Case
        ↓
Implement Infrastructure / Presentation Adapter
        ↓
Run Automated Test Suite (Passing)
        ↓
Run Formatter & Linter (Ruff)
        ↓
Run Type Checker (Pyrefly)
        ↓
Commit with Gitmoji & Conventional Commits
```

---

## Environment Setup

The repository uses [uv](https://docs.astral.sh/uv/) for high-speed, reproducible Python virtual environment and dependency management.

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

Copy the environment template and verify settings:

```bash
cp .env.example .env
```

### 3. Apply Migrations

```bash
uv run python manage.py migrate
```

---

## Testing Strategy

### Test Hierarchy

Tests are categorized into explicit directories based on test scope and execution speed:

```text
tests/
├── unit/                      # Isolated, in-memory unit tests (Fastest)
│   ├── domain/                # Entity, Value Object, Domain Service invariants
│   ├── application/           # Use Cases orchestrated with in-memory Fakes
│   └── presentation/          # Dependency injection container resolution
│
├── integration/               # Real database infrastructure tests
│   ├── django/                # Django ORM models, admins, repositories
│   └── workflows/             # Multi-step business workflows (lifecycle, deletion)
│
├── api/                       # DRF endpoints, serializers, HTTP status codes
└── e2e/                       # Complete cross-domain end-to-end user journeys
```

### Executing Tests

Run tests using `pytest` via `uv`:

```bash
# Execute entire test suite
uv run pytest

# Run only unit tests
uv run pytest tests/unit/

# Run integration tests against database
uv run pytest tests/integration/

# Run API endpoint tests
uv run pytest tests/api/

# Run end-to-end workflow tests
uv run pytest tests/e2e/

# Run a specific test module
uv run pytest tests/unit/domain/test_gap_analysis_service.py

# Run a specific test case by expression
uv run pytest -k "test_should_calculate_competency_gap"

# Run tests with detailed code coverage report
uv run pytest --cov=src --cov-report=term-missing --cov-report=html
```

### Test Doubles & Fakes

Per `AGENTS.md` section 28, follow the priority order:
$$\text{Fake} \succ \text{Stub} \succ \text{Mock}$$

- Use **Fakes** (in-memory repositories with dictionaries) for application use case testing. Refer to `tests/unit/application/use_cases/fakes.py`.
- Reserve mock frameworks only for verifying interactions that cannot be checked via observable state changes.

### Test Naming Conventions

Test names must clearly describe the expected behavior and scenario:

- `test_should_calculate_competency_gap_when_measurement_below_requirement`
- `test_should_prevent_deletion_when_competency_referenced_in_path`
- `test_should_transition_status_from_draft_to_accepted`

Avoid ambiguous names like `test_case1`, `test_competency`, or `test_delete`.

---

## Code Formatting & Linting

The repository uses [Ruff](https://astral.sh/ruff) as the unified formatter and linter.

### Formatting

Code must strictly comply with PEP 8 and an **88-character line length limit**:

```bash
# Automatically format all files in place
uv run ruff format .

# Check formatting without modifying files
uv run ruff format --check .
```

### Linting

Run the linter to verify import sorting, naming conventions, docstrings, and syntax:

```bash
# Check code for linting violations
uv run ruff check .

# Automatically apply safe fixes
uv run ruff check --fix .
```

---

## Static Type Checking

Static type safety is verified using [Pyrefly](https://github.com/pyrefly).

- All domain entities, value objects, use cases, ports, and DTOs must have explicit type annotations.
- Unnecessary `Any` types and `# type: ignore` directives are strictly prohibited unless interacting with dynamic framework edge cases.

```bash
# Execute static type checking
uv run pyrefly check
```

---

## Pre-Commit Quality Gate

Before committing changes, execute the full quality verification sequence:

```bash
uv run pytest
uv run ruff format .
uv run ruff check .
uv run pyrefly check
```

Alternatively, run the pre-commit script if installed (see [Git Hooks](#git-flow--commit-standards)).

---

## Git Flow & Commit Standards

### Branching Model

- `main`: Production-ready releases.
- `develop`: Integration branch for active features.
- `feature/<name>`: Feature branches branched off and merged back into `develop`.

### Commit Convention

Commits must follow **Conventional Commits** paired with **Gitmoji**:

```text
<gitmoji> <type>(<optional scope>): <description>
```

| Type | Gitmoji | Meaning |
|---|---|---|
| `feat` | ✨ `:sparkles:` | Introducing a new feature |
| `fix` | 🐛 `:bug:` | Fixing a bug |
| `test` | ✅ `:white_check_mark:` | Adding or updating tests |
| `refactor` | ♻️ `:recycle:` | Refactoring code without altering external behavior |
| `docs` | 📝 `:memo:` | Adding or updating documentation |
| `style` | 🎨 `:art:` | Improving structure or formatting of code |
| `perf` | ⚡ `:zap:` | Improving performance |
| `chore` | 🔧 `:wrench:` | Tooling, configuration, or dependency updates |

#### Examples

```bash
git commit -m "✨ feat: implement competency gap analysis use case"
git commit -m "✅ test: add unhappy path for contested evaluations"
git commit -m "📝 docs: document API endpoints and query parameters"
git commit -m "🐛 fix: handle null previous level on initial competency evaluation"
```
