# Spec Delta

## Purpose

Manages employee records and their career path enrollments, enforcing business rules around active path selection and enrollment history.

## ADDED Requirements

### Requirement: Register collaborator information

The system SHALL store essential collaborator information including unique identifier, name, email, and department.

#### Scenario: Create new collaborator

- **WHEN** admin registers collaborator with name "João Silva", email "joao.silva@company.com", department "Engineering"
- **THEN** system creates collaborator record with unique identifier

#### Scenario: Enforce unique email

- **WHEN** admin attempts to register collaborator with email already in use
- **THEN** system rejects the operation with duplicate email error

### Requirement: Enroll collaborator in career path

The system SHALL allow enrolling collaborators in career paths with specified target level, recording enrollment date and active status.

#### Scenario: Create path enrollment

- **WHEN** admin enrolls collaborator in "Software Engineer Track" targeting "Senior" level
- **THEN** system creates enrollment record with enrollment date and inactive status by default

#### Scenario: Prevent duplicate path enrollment

- **WHEN** collaborator attempts to enroll in path they are already enrolled in
- **THEN** system rejects the operation indicating existing enrollment

### Requirement: Enforce single active path

The system SHALL enforce that only one path enrollment can be active at any time for each collaborator.

#### Scenario: Activate path enrollment

- **WHEN** admin activates "Software Engineer Track" enrollment for collaborator with no other active paths
- **THEN** system sets the enrollment as active

#### Scenario: Automatic deactivation on activation

- **WHEN** admin activates "Technical Leadership Track" while "Software Engineer Track" is already active
- **THEN** system deactivates the previous active path and activates the new one

#### Scenario: Query active path

- **WHEN** user requests collaborator's active career path
- **THEN** system returns the single currently active enrollment or null if none active

### Requirement: Track enrollment history

The system SHALL maintain complete history of all path enrollments including past enrollments even when no longer active.

#### Scenario: List all enrollments

- **WHEN** user requests collaborator's complete enrollment history
- **THEN** system returns all enrollments with dates and active status

#### Scenario: Preserve inactive enrollments

- **WHEN** collaborator switches active path
- **THEN** system maintains the previous enrollment record as inactive

### Requirement: Update target level

The system SHALL allow updating the target level within an existing enrollment without creating new enrollment.

#### Scenario: Change target level

- **WHEN** admin changes enrollment target from "Mid-Level" to "Senior"
- **THEN** system updates the target level while preserving enrollment date and history

#### Scenario: Validate target level exists

- **WHEN** admin attempts to set target level that does not exist in the path
- **THEN** system rejects the operation with invalid level error

### Requirement: Query collaborators by path

The system SHALL allow querying which collaborators are enrolled in specific career paths.

#### Scenario: List enrolled collaborators

- **WHEN** user requests all collaborators enrolled in "Software Engineer Track"
- **THEN** system returns list with enrollment details and active status

#### Scenario: Filter by active enrollments only

- **WHEN** user requests only active enrollments for a path
- **THEN** system returns filtered list of collaborators with active status

### Requirement: Remove enrollment

The system SHALL allow removing path enrollment only if no evaluations reference the enrollment period.

#### Scenario: Remove enrollment without evaluations

- **WHEN** admin removes enrollment with no associated evaluations
- **THEN** system successfully deletes the enrollment record

#### Scenario: Prevent removal with evaluations

- **WHEN** admin attempts to remove enrollment that has evaluation history
- **THEN** system rejects deletion indicating evaluations must be preserved
