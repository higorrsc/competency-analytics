# Spec Delta

## Purpose

Provides temporal views of competency evolution over time through optimized read models, enabling trend analysis and career progression monitoring.

## ADDED Requirements

### Requirement: Query competency level history

The system SHALL provide history of competency level changes across evaluations ordered chronologically.

#### Scenario: Retrieve competency history for collaborator

- **WHEN** user requests Python competency history for collaborator "João Silva"
- **THEN** system returns list of measurements from all finalized evaluations with dates, periods, and levels

#### Scenario: Calculate level changes between evaluations

- **WHEN** user requests competency history
- **THEN** system includes previous level and level change (+1, -1, 0) for each evaluation

#### Scenario: Show only finalized evaluations

- **WHEN** collaborator has mix of RASCUNHO, CONCLUÍDA, ACEITA, and CONTESTADA evaluations
- **THEN** history includes only ACEITA and CONTESTADA evaluations

### Requirement: Compare evaluations across periods

The system SHALL allow comparing competency levels between two specific evaluation periods.

#### Scenario: Compare two evaluation periods

- **WHEN** user compares Q1 2025 evaluation with Q1 2026 evaluation
- **THEN** system returns competencies measured in both with level changes

#### Scenario: Handle missing measurements

- **WHEN** competency measured in Q1 2026 but not in Q1 2025
- **THEN** system indicates competency as newly measured rather than showing change

### Requirement: Visualize competency trends

The system SHALL identify trends (improving, stable, declining) for competencies measured across multiple evaluations.

#### Scenario: Detect improvement trend

- **WHEN** competency measured at level 2, then 3, then 4 across three evaluations
- **THEN** system classifies as improving trend with +2 total change

#### Scenario: Detect declining trend

- **WHEN** competency measured at level 5, then 4, then 3 across three evaluations
- **THEN** system classifies as declining trend with -2 total change

#### Scenario: Detect stable competency

- **WHEN** competency measured at level 4 consistently across three evaluations
- **THEN** system classifies as stable with 0 total change

### Requirement: Calculate path progression summary

The system SHALL calculate progression toward target path level showing percentage of requirements met based on latest evaluation.

#### Scenario: Calculate completion percentage

- **WHEN** collaborator targets "Senior" level with 10 competency requirements and meets 7
- **THEN** system returns 70% completion toward target level

#### Scenario: Weight requirements in calculation

- **WHEN** calculating progression
- **THEN** system counts CORE, IMPORTANT, and DESIRABLE requirements equally in percentage

#### Scenario: Track progress over time

- **WHEN** user requests path progression history
- **THEN** system shows completion percentage for each evaluation period

### Requirement: Aggregate competency data across collaborators

The system SHALL provide aggregate views of competency levels across multiple collaborators for department or team analysis.

#### Scenario: Calculate average competency level for team

- **WHEN** manager requests Python competency for Engineering department
- **THEN** system returns average level from all members' latest finalized evaluations

#### Scenario: Identify team competency gaps

- **WHEN** manager compares team against required path level
- **THEN** system shows which competencies are below target across the team

### Requirement: Query using optimized database views

The system SHALL use database views for complex temporal queries rather than loading all evaluation entities into memory.

#### Scenario: History query uses database view

- **WHEN** user requests competency history spanning 3 years with 20 evaluations
- **THEN** system queries pre-computed database view returning results efficiently

#### Scenario: Aggregation uses database view

- **WHEN** calculating team-level statistics across 100 collaborators
- **THEN** system uses database view with aggregation functions

### Requirement: Filter history by date range

The system SHALL allow filtering competency history by start date and end date.

#### Scenario: Query specific time range

- **WHEN** user requests competency history from 2025-01-01 to 2025-12-31
- **THEN** system returns only evaluations within that date range

#### Scenario: Query last N evaluations

- **WHEN** user requests last 3 evaluations for competency analysis
- **THEN** system returns 3 most recent finalized evaluations

### Requirement: Export temporal data for reporting

The system SHALL support exporting competency history and progression data in structured format for external analysis.

#### Scenario: Export collaborator history

- **WHEN** user exports competency history for collaborator
- **THEN** system provides structured data with evaluation dates, competencies, levels, and changes

#### Scenario: Export team progression summary

- **WHEN** manager exports team path progression
- **THEN** system provides data showing each member's progression percentage and target level

### Requirement: Handle contested evaluations in trends

The system SHALL include CONTESTADA evaluations in temporal analysis since they represent finalized assessment even if disputed.

#### Scenario: Include contested evaluation in history

- **WHEN** collaborator has sequence: ACEITA, CONTESTADA, ACEITA
- **THEN** system includes all three in competency trend calculation

#### Scenario: Flag contested evaluations in results

- **WHEN** history includes CONTESTADA evaluation
- **THEN** system indicates the evaluation was contested in the returned data
