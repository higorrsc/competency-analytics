# career-paths Specification

## Purpose
Defines career progression paths with hierarchical levels and competency requirements, enabling organizations to establish clear skill expectations for each career stage.

## Requirements

### Requirement: Create career path structure

The system SHALL support creating career paths with multiple ordered levels, where each level has a name and sequential order.

#### Scenario: Create path with levels

- **WHEN** admin creates path "Software Engineer Track" with levels "Junior" (order 1), "Mid-Level" (order 2), "Senior" (order 3)
- **THEN** system stores the path structure with ordered levels available for assignment

#### Scenario: Enforce sequential level ordering

- **WHEN** admin attempts to create levels with non-sequential order (1, 2, 4)
- **THEN** system rejects the operation requiring continuous sequential ordering

### Requirement: Define competency requirements per level

Each path level SHALL define competency requirements specifying competency, minimum proficiency level (1-5), and weight (CORE, IMPORTANT, DESIRABLE).

#### Scenario: Add competency requirements to level

- **WHEN** admin adds requirements to "Senior" level: Python (minimum 4, CORE), Leadership (minimum 3, IMPORTANT)
- **THEN** system stores requirements for gap analysis and progression eligibility

#### Scenario: Validate minimum level range

- **WHEN** admin attempts to set minimum level to 6 or 0
- **THEN** system rejects the operation requiring level between 1 and 5

#### Scenario: Require valid competency reference

- **WHEN** admin attempts to add requirement referencing non-existent competency
- **THEN** system rejects the operation with competency not found error

### Requirement: Categorize requirement importance

The system SHALL support three requirement weight categories: CORE (essential), IMPORTANT (strongly recommended), DESIRABLE (nice to have).

#### Scenario: Set requirement weights

- **WHEN** admin defines "Python" as CORE and "Docker" as DESIRABLE for "Senior" level
- **THEN** system stores weights for prioritization in gap analysis

#### Scenario: Query requirements by weight

- **WHEN** user requests only CORE requirements for a path level
- **THEN** system returns filtered list of essential competencies

### Requirement: Prevent level deletion with active enrollments

The system SHALL prevent deletion of path levels that are currently targeted by any collaborator enrollments.

#### Scenario: Block deletion with active targets

- **WHEN** admin attempts to delete "Senior" level with 5 collaborators targeting it
- **THEN** system rejects deletion listing the number of affected enrollments

#### Scenario: Allow deletion of untargeted level

- **WHEN** admin deletes a level with no collaborator enrollments targeting it
- **THEN** system successfully removes the level and its requirements

### Requirement: Update path without breaking enrollments

The system SHALL allow updating path names and level descriptions while preserving existing collaborator enrollments.

#### Scenario: Rename path

- **WHEN** admin renames path from "Engineering Track" to "Software Engineering Track"
- **THEN** system updates the name while maintaining all existing enrollments

#### Scenario: Update level requirements

- **WHEN** admin adds new requirement to "Senior" level
- **THEN** system updates requirements affecting future gap calculations for enrolled collaborators

### Requirement: Query path structures

The system SHALL allow querying complete path structures including all levels and their competency requirements.

#### Scenario: Retrieve complete path definition

- **WHEN** user requests path "Software Engineer Track"
- **THEN** system returns path with all levels in order and complete requirement details

#### Scenario: List all available paths

- **WHEN** user requests all career paths
- **THEN** system returns list of all paths with basic information

### Requirement: Validate unique level names within path

The system SHALL enforce unique level names within each career path.

#### Scenario: Prevent duplicate level names

- **WHEN** admin attempts to create two levels named "Senior" in the same path
- **THEN** system rejects the operation with uniqueness constraint error

#### Scenario: Allow same level name across paths

- **WHEN** admin creates "Senior" level in both "Engineering Track" and "Management Track"
- **THEN** system allows both as they are in different paths
