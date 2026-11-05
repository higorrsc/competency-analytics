# REST API Reference Documentation

The **Personnel Competency Analysis System** provides a RESTful HTTP API conforming to JSON and OpenAPI 3.0 standards.

Interactive documentation and testing consoles are available at:
- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`
- **OpenAPI Schema**: `/api/schema/`

---

## Table of Contents

- [General Conventions](#general-conventions)
- [Error Response Format](#error-response-format)
- [Categories API](#categories-api)
- [Competencies API](#competencies-api)
- [Career Paths API](#career-paths-api)
- [Collaborators API](#collaborators-api)
- [Evaluations API](#evaluations-api)
- [Analytics & Reporting Endpoints](#analytics--reporting-endpoints)
  - [Competency Gap Analysis](#competency-gap-analysis)
  - [Competency History View](#competency-history-view)
  - [Path Progression View](#path-progression-view)

---

## General Conventions

- **Base URL**: `/api/v1`
- **Content Type**: `application/json`
- **Timezone**: Timestamps are expressed in ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ`).
- **Identifiers**: Entity IDs are standard UUIDv4 strings.

---

## Error Response Format

All error responses return a structured JSON payload:

```json
{
  "status_code": 400,
  "error_type": "ValidationError",
  "detail": "Invalid input payload",
  "errors": {
    "name": ["This field may not be blank."]
  }
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|---|---|---|
| `200 OK` | Success | Request succeeded with data payload. |
| `201 Created` | Created | Resource successfully created. |
| `204 No Content`| No Content | Action succeeded with no body returned. |
| `400 Bad Request` | Bad Request | Validation error or malformed payload. |
| `404 Not Found` | Not Found | Requested resource was not found. |
| `409 Conflict` | Conflict | Business invariant violation (e.g. deleting referenced competency). |

---

## Categories API

### List Categories
- **`GET /api/v1/categories/`**
- **Response `200 OK`**:
```json
[
  {
    "id": "c138b329-87a7-474c-bd08-8e6f1a8b9e67",
    "name": "Engineering",
    "description": "Technical software and infrastructure competencies"
  }
]
```

### Create Category
- **`POST /api/v1/categories/`**
- **Request Body**:
```json
{
  "name": "Engineering",
  "description": "Technical software and infrastructure competencies"
}
```
- **Response `201 Created`**:
```json
{
  "id": "c138b329-87a7-474c-bd08-8e6f1a8b9e67",
  "name": "Engineering",
  "description": "Technical software and infrastructure competencies"
}
```

---

## Competencies API

### List Competencies
- **`GET /api/v1/competencies/`**
- **Query Parameters**:
  - `category_id` (UUID, optional): Filter by category.
  - `group_id` (UUID, optional): Filter by competency group.
- **Response `200 OK`**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Python Backend Development",
    "description": "Async services, Django, architectural patterns",
    "category_id": "c138b329-87a7-474c-bd08-8e6f1a8b9e67",
    "group_id": "d270381e-d450-4828-b807-68b35582fef5",
    "level_descriptions": {
      "1": "Basic script authoring and syntax understanding",
      "2": "REST APIs with standard frameworks",
      "3": "Async programming and clean domain boundaries",
      "4": "Architectural leadership and performance tuning",
      "5": "Enterprise scale and core runtime mastery"
    }
  }
]
```

### Create Competency
- **`POST /api/v1/competencies/`**
- **Request Body**:
```json
{
  "name": "Python Backend Development",
  "description": "Async services, Django, architectural patterns",
  "category_id": "c138b329-87a7-474c-bd08-8e6f1a8b9e67",
  "group_id": "d270381e-d450-4828-b807-68b35582fef5",
  "level_descriptions": {
    "1": "Basic script authoring and syntax understanding",
    "2": "REST APIs with standard frameworks",
    "3": "Async programming and clean domain boundaries",
    "4": "Architectural leadership and performance tuning",
    "5": "Enterprise scale and core runtime mastery"
  }
}
```
- **Response `201 Created`**: Returns the created competency resource.

### Delete Competency
- **`DELETE /api/v1/competencies/{id}/`**
- **Response `204 No Content`**: Successfully deleted when unreferenced.
- **Response `409 Conflict`**: Returned when the competency is referenced by a path level or evaluation:
```json
{
  "status_code": 409,
  "error_type": "ConflictError",
  "detail": "Competency 550e8400-e29b-41d4-a716-446655440000 is referenced and cannot be deleted: ['Competency is referenced in career paths']"
}
```

---

## Career Paths API

### List Career Paths
- **`GET /api/v1/paths/`**
- **Response `200 OK`**:
```json
[
  {
    "id": "7134267e-2cf8-410a-ae8d-7a3028ee8d34",
    "name": "Backend Software Engineer",
    "description": "Progressive path from Junior to Staff Backend Engineer",
    "levels": [
      {
        "id": "8939c065-a868-450f-a496-0df8faaa8230",
        "name": "Junior Engineer",
        "order": 1,
        "requirements": [
          {
            "competency_id": "550e8400-e29b-41d4-a716-446655440000",
            "minimum_level": 2,
            "weight": "MANDATORY"
          }
        ]
      }
    ]
  }
]
```

### Create Career Path
- **`POST /api/v1/paths/`**
- **Request Body**:
```json
{
  "name": "Backend Software Engineer",
  "description": "Progressive path from Junior to Staff Backend Engineer",
  "levels": [
    {
      "name": "Junior Engineer",
      "order": 1,
      "requirements": [
        {
          "competency_id": "550e8400-e29b-41d4-a716-446655440000",
          "minimum_level": 2,
          "weight": "MANDATORY"
        }
      ]
    }
  ]
}
```

---

## Collaborators API

### List Collaborators
- **`GET /api/v1/collaborators/`**

### Create Collaborator
- **`POST /api/v1/collaborators/`**
- **Request Body**:
```json
{
  "name": "Carlos Silva",
  "email": "carlos.silva@corp.com",
  "department": "Engineering"
}
```

### Enroll Collaborator in Career Path
- **`POST /api/v1/collaborators/{id}/enroll/`**
- Enrolls collaborator in a career path. Automatically deactivates previously active enrollments.
- **Request Body**:
```json
{
  "path_id": "7134267e-2cf8-410a-ae8d-7a3028ee8d34",
  "enrollment_date": "2025-01-10T09:00:00Z"
}
```
- **Response `200 OK`**: Returns updated collaborator with active enrollment.

---

## Evaluations API

### Create Evaluation (Draft)
- **`POST /api/v1/evaluations/`**
- **Request Body**:
```json
{
  "collaborator_id": "673cf97e-1314-41e7-a9a7-98782a3b0fa4",
  "evaluator_id": "89b53da1-6f01-4475-bf51-c049449fdf67",
  "period": "2025.H1",
  "evaluation_date": "2025-06-30T18:00:00Z",
  "measurements": [
    {
      "competency_id": "550e8400-e29b-41d4-a716-446655440000",
      "current_level": 3
    }
  ]
}
```
- **Response `201 Created`**:
```json
{
  "id": "1893c5d6-c1be-497c-9b16-52c6f6004940",
  "collaborator_id": "673cf97e-1314-41e7-a9a7-98782a3b0fa4",
  "evaluator_id": "89b53da1-6f01-4475-bf51-c049449fdf67",
  "period": "2025.H1",
  "evaluation_date": "2025-06-30T18:00:00Z",
  "status": "DRAFT",
  "measurements": [
    {
      "competency_id": "550e8400-e29b-41d4-a716-446655440000",
      "current_level": 3
    }
  ]
}
```

### Submit Evaluation
- **`POST /api/v1/evaluations/{id}/submit/`**
- Advances status to `COMPLETED`. Measurements become permanently immutable.

### Accept Evaluation
- **`POST /api/v1/evaluations/{id}/accept/`**
- Request Body (optional notes):
```json
{
  "notes": "Evaluation accepted without objections."
}
```
- Transitions status to `ACCEPTED`.

### Contest Evaluation
- **`POST /api/v1/evaluations/{id}/contest/`**
- Request Body (`notes` is strictly mandatory):
```json
{
  "notes": "Dispute on level 3 requirement for system architecture."
}
```
- Transitions status to `CONTESTED`.

---

## Analytics & Reporting Endpoints

### Competency Gap Analysis
Calculates the proficiency gap against a specific path level or against the collaborator's active path progression level. Unmeasured competencies default to level 0.

- **`GET /api/v1/collaborators/{id}/gap-analysis/`**
- **Query Parameters**:
  - `target_level_id` (UUID, optional): Specify explicit target path level. Defaults to active enrolled level.
- **Response `200 OK`**:
```json
{
  "path_id": "7134267e-2cf8-410a-ae8d-7a3028ee8d34",
  "path_level_id": "8939c065-a868-450f-a496-0df8faaa8230",
  "evaluation_id": "1893c5d6-c1be-497c-9b16-52c6f6004940",
  "overall_match_percentage": 75.0,
  "is_eligible_for_promotion": false,
  "gaps": [
    {
      "competency_id": "550e8400-e29b-41d4-a716-446655440000",
      "required_level": 4,
      "measured_level": 3,
      "gap": 1,
      "weight": "MANDATORY"
    }
  ]
}
```

---

### Competency History View
Optimized query over historical evaluations with chronological ordering and delta calculations.

- **`GET /api/v1/collaborators/{id}/history/`**
- **Query Parameters**:
  - `competency_id` (UUID, optional): Filter by single competency.
  - `start_date` (Date, optional, `YYYY-MM-DD`): Earliest evaluation date.
  - `end_date` (Date, optional, `YYYY-MM-DD`): Latest evaluation date.
- **Response `200 OK`**:
```json
[
  {
    "collaborator_id": "673cf97e-1314-41e7-a9a7-98782a3b0fa4",
    "competency_id": "550e8400-e29b-41d4-a716-446655440000",
    "competency_name": "Python Backend Development",
    "period": "2024.H2",
    "evaluation_date": "2024-12-15T10:00:00Z",
    "current_level": 2,
    "previous_level": null,
    "level_change": null,
    "evaluator_name": "Senior Staff Engineer"
  },
  {
    "collaborator_id": "673cf97e-1314-41e7-a9a7-98782a3b0fa4",
    "competency_id": "550e8400-e29b-41d4-a716-446655440000",
    "competency_name": "Python Backend Development",
    "period": "2025.H1",
    "evaluation_date": "2025-06-30T18:00:00Z",
    "current_level": 3,
    "previous_level": 2,
    "level_change": 1,
    "evaluator_name": "Senior Staff Engineer"
  }
]
```

---

### Path Progression View
Database view summarizing collaborator progress on their active career path.

- **`GET /api/v1/collaborators/{id}/progression/`**
- **Response `200 OK`**:
```json
{
  "collaborator_id": "673cf97e-1314-41e7-a9a7-98782a3b0fa4",
  "path_id": "7134267e-2cf8-410a-ae8d-7a3028ee8d34",
  "path_name": "Backend Software Engineer",
  "current_level_name": "Mid-level Engineer",
  "current_level_order": 2,
  "mandatory_requirements_met": 4,
  "mandatory_requirements_total": 5,
  "optional_requirements_met": 2,
  "optional_requirements_total": 2,
  "completion_percentage": 85.7,
  "is_eligible_for_advancement": false
}
```
