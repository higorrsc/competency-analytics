# Spec Delta

## Purpose

Provides a hierarchical catalog of competencies organized by categories and groups, with detailed proficiency level descriptions for assessing employee skills.

## ADDED Requirements

### Requirement: Create competency hierarchy

The system SHALL support a three-level competency hierarchy: Category contains CompetencyGroups, which contain individual Competencies.

#### Scenario: Create complete hierarchy

- **WHEN** admin creates Category "Technical Skills" with CompetencyGroup "Programming" containing Competency "Python"
- **THEN** system stores the three-level hierarchy and makes it available for evaluation and path definition

#### Scenario: Enforce hierarchy structure

- **WHEN** admin attempts to create a Competency without a parent CompetencyGroup
- **THEN** system rejects the operation with validation error

### Requirement: Define proficiency levels

Each competency SHALL define exactly 5 proficiency levels (1-5) with textual descriptions for each level.

#### Scenario: Define level descriptions

- **WHEN** admin creates Competency "Python" with descriptions for levels 1-5
- **THEN** system stores all level descriptions and displays them during evaluation

#### Scenario: Enforce all levels defined

- **WHEN** admin attempts to save a competency with missing level descriptions
- **THEN** system rejects the operation requiring all 5 levels to be described

### Requirement: Prevent deletion of referenced competencies

The system SHALL prevent deletion of competencies that are referenced by career paths or have measurements in evaluations.

#### Scenario: Block deletion with path references

- **WHEN** admin attempts to delete a competency that is required by a career path level
- **THEN** system rejects deletion with error message listing referencing paths

#### Scenario: Block deletion with evaluation measurements

- **WHEN** admin attempts to delete a competency that has measurements in any evaluation
- **THEN** system rejects deletion with error message indicating existing measurements

#### Scenario: Allow deletion of unreferenced competency

- **WHEN** admin deletes a competency with no path references or evaluation measurements
- **THEN** system successfully removes the competency and its hierarchy relationships

### Requirement: Query competencies by hierarchy

The system SHALL allow querying competencies by category, group, or individual competency level.

#### Scenario: List competencies by category

- **WHEN** user requests all competencies in Category "Technical Skills"
- **THEN** system returns all groups and competencies under that category

#### Scenario: List competencies by group

- **WHEN** user requests all competencies in CompetencyGroup "Programming"
- **THEN** system returns all competencies in that group with their level descriptions

### Requirement: Update competency definitions

The system SHALL allow updating competency names, descriptions, and level descriptions without breaking existing references.

#### Scenario: Update competency name

- **WHEN** admin updates competency name from "Python" to "Python Programming"
- **THEN** system updates the name while preserving all path requirements and evaluation measurements

#### Scenario: Update level descriptions

- **WHEN** admin revises level descriptions for a competency
- **THEN** system updates descriptions for future evaluations while preserving historical evaluation data

### Requirement: Validate competency uniqueness

The system SHALL enforce unique competency names within the same CompetencyGroup.

#### Scenario: Prevent duplicate competency names

- **WHEN** admin attempts to create competency "Python" in group "Programming" where it already exists
- **THEN** system rejects the operation with uniqueness constraint error

#### Scenario: Allow same name in different groups

- **WHEN** admin creates competency "Leadership" in group "Management" and also in group "Technical"
- **THEN** system allows both as they are in different groups
