# Spec Delta

## Purpose

Manages formal competency evaluation workflow from draft creation through employee response, ensuring immutable historical records once finalized.

## ADDED Requirements

### Requirement: Create evaluation in draft state

The system SHALL allow evaluators to create evaluations in RASCUNHO (draft) state with evaluation period, date, and collaborator reference.

#### Scenario: Create new evaluation

- **WHEN** evaluator creates evaluation for collaborator "João Silva" for period "Q1 2026"
- **THEN** system creates evaluation in RASCUNHO state with current date and evaluator reference

#### Scenario: One active draft per collaborator per period

- **WHEN** evaluator attempts to create second draft evaluation for same collaborator and period
- **THEN** system rejects the operation indicating existing draft for that period

### Requirement: Add competency measurements to draft

The system SHALL allow adding competency measurements with level (1-5), notes, and evidence only while evaluation is in RASCUNHO state.

#### Scenario: Add measurement to draft

- **WHEN** evaluator adds measurement for competency "Python" with level 4, notes "Strong backend skills"
- **THEN** system stores measurement associated with the evaluation

#### Scenario: Validate measurement level range

- **WHEN** evaluator attempts to set measurement level to 0 or 6
- **THEN** system rejects the operation requiring level between 1 and 5

#### Scenario: Require valid competency reference

- **WHEN** evaluator attempts to measure non-existent competency
- **THEN** system rejects the operation with competency not found error

### Requirement: Edit measurements in draft state

The system SHALL allow modifying or removing measurements only while evaluation remains in RASCUNHO state.

#### Scenario: Update measurement in draft

- **WHEN** evaluator changes Python measurement from level 4 to level 5 in draft evaluation
- **THEN** system updates the measurement

#### Scenario: Block measurement edit after completion

- **WHEN** evaluator attempts to modify measurement in evaluation with status CONCLUÍDA or ACEITA or CONTESTADA
- **THEN** system rejects the operation indicating evaluation is immutable

### Requirement: Submit evaluation for review

The system SHALL allow evaluator to submit evaluation changing status from RASCUNHO to CONCLUÍDA, requiring at least one measurement.

#### Scenario: Submit evaluation with measurements

- **WHEN** evaluator submits draft evaluation containing 5 competency measurements
- **THEN** system changes status to CONCLUÍDA and records submission date

#### Scenario: Reject submission without measurements

- **WHEN** evaluator attempts to submit evaluation with zero measurements
- **THEN** system rejects the operation requiring at least one measurement

### Requirement: Employee accepts evaluation

The system SHALL allow collaborator to accept completed evaluation, changing status from CONCLUÍDA to ACEITA and making it permanently immutable.

#### Scenario: Accept evaluation

- **WHEN** collaborator accepts evaluation in CONCLUÍDA state with optional response notes
- **THEN** system changes status to ACEITA, records response date and notes, and locks evaluation permanently

#### Scenario: Block acceptance of non-completed evaluation

- **WHEN** collaborator attempts to accept evaluation in RASCUNHO state
- **THEN** system rejects the operation requiring CONCLUÍDA status

### Requirement: Employee contests evaluation

The system SHALL allow collaborator to contest completed evaluation, changing status from CONCLUÍDA to CONTESTADA with required contestation notes.

#### Scenario: Contest evaluation with notes

- **WHEN** collaborator contests evaluation with notes "Disagree with Python assessment, recent projects not considered"
- **THEN** system changes status to CONTESTADA, records response date and notes, and locks evaluation permanently

#### Scenario: Require contestation notes

- **WHEN** collaborator attempts to contest evaluation without providing notes
- **THEN** system rejects the operation requiring contestation explanation

### Requirement: Enforce evaluation immutability

The system SHALL make evaluations completely immutable once status is ACEITA or CONTESTADA, preventing any modifications to measurements, notes, or status.

#### Scenario: Block any modification to accepted evaluation

- **WHEN** any user attempts to modify accepted evaluation measurements, notes, or status
- **THEN** system rejects all modification operations indicating evaluation is finalized

#### Scenario: Block status change from finalized state

- **WHEN** admin attempts to change status from ACEITA back to CONCLUÍDA
- **THEN** system rejects the operation indicating finalized evaluations cannot be reopened

### Requirement: Query evaluations by collaborator

The system SHALL allow querying evaluations by collaborator with filtering by status and period.

#### Scenario: List collaborator evaluations

- **WHEN** user requests all evaluations for collaborator "João Silva"
- **THEN** system returns evaluations ordered by date descending

#### Scenario: Filter by status

- **WHEN** user requests only ACEITA evaluations for collaborator
- **THEN** system returns filtered list of accepted evaluations

#### Scenario: Filter by period

- **WHEN** user requests evaluations for period "Q1 2026"
- **THEN** system returns evaluations matching that period

### Requirement: Query evaluations by evaluator

The system SHALL allow querying which evaluations were conducted by specific evaluator.

#### Scenario: List evaluator's evaluations

- **WHEN** manager requests all evaluations they conducted
- **THEN** system returns list with collaborator names, periods, and status

#### Scenario: Filter pending evaluator actions

- **WHEN** manager requests only RASCUNHO evaluations
- **THEN** system returns drafts awaiting completion

### Requirement: Retrieve complete evaluation details

The system SHALL allow retrieving complete evaluation including all measurements with competency details, notes, and evidence.

#### Scenario: Get evaluation with measurements

- **WHEN** user requests evaluation by ID
- **THEN** system returns evaluation with all measurements including competency names, levels, notes, and evidence
