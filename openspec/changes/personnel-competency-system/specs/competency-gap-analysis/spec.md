# Spec Delta

## Purpose

Calculates gaps between current competency levels and career path requirements, producing prioritized development recommendations to guide employee growth.

## ADDED Requirements

### Requirement: Calculate competency gaps from evaluation

The system SHALL calculate gaps by comparing competency levels from latest accepted evaluation against requirements from target path level.

#### Scenario: Calculate gap for met requirement

- **WHEN** collaborator has Python level 5 and target path level requires Python minimum 4
- **THEN** system calculates gap as 0 indicating requirement is met

#### Scenario: Calculate gap for unmet requirement

- **WHEN** collaborator has Python level 2 and target path level requires Python minimum 4
- **THEN** system calculates gap as 2 levels indicating development needed

#### Scenario: Calculate gap for unmeasured competency

- **WHEN** target path requires competency "Docker" but latest evaluation has no Docker measurement
- **THEN** system calculates gap as full required level indicating competency not yet assessed

### Requirement: Use only finalized evaluations

The system SHALL use only evaluations with status ACEITA or CONTESTADA for gap calculation, ignoring draft and pending evaluations.

#### Scenario: Ignore draft evaluations

- **WHEN** collaborator has RASCUNHO evaluation with measurements but no finalized evaluations
- **THEN** system indicates no evaluation available for gap analysis

#### Scenario: Use most recent finalized evaluation

- **WHEN** collaborator has multiple ACEITA evaluations from different periods
- **THEN** system uses the evaluation with the most recent evaluation date

### Requirement: Prioritize gaps by requirement weight

The system SHALL order gaps by requirement weight (CORE first, then IMPORTANT, then DESIRABLE) with secondary ordering by gap size.

#### Scenario: Sort by weight then gap size

- **WHEN** collaborator has gap 2 in DESIRABLE competency and gap 1 in CORE competency
- **THEN** system returns CORE gap first despite smaller gap size

#### Scenario: Sort same weight by gap size

- **WHEN** collaborator has two CORE competency gaps of 3 levels and 1 level
- **THEN** system returns larger gap (3 levels) before smaller gap (1 level)

### Requirement: Generate development recommendations

The system SHALL generate textual recommendations for each gap based on gap size and requirement weight.

#### Scenario: Recommend immediate action for large core gaps

- **WHEN** collaborator has 3-level gap in CORE competency
- **THEN** system generates recommendation indicating high priority development needed

#### Scenario: Recommend maintenance for met requirements

- **WHEN** collaborator meets or exceeds all CORE requirements
- **THEN** system generates recommendation to maintain current competency levels

### Requirement: Calculate overall progression eligibility

The system SHALL determine if collaborator meets minimum criteria to progress to target level based on CORE requirement gaps.

#### Scenario: Eligible when all core requirements met

- **WHEN** collaborator has zero gaps in all CORE requirements regardless of IMPORTANT gaps
- **THEN** system indicates eligible for progression to target level

#### Scenario: Not eligible with any core gaps

- **WHEN** collaborator has 1-level gap in any CORE requirement
- **THEN** system indicates not eligible and lists blocking competencies

### Requirement: Compare against specific path level

The system SHALL calculate gaps against explicitly specified target path level, not just collaborator's currently enrolled target.

#### Scenario: Calculate gaps for next level

- **WHEN** collaborator currently targets "Mid-Level" but requests gap analysis for "Senior"
- **THEN** system calculates gaps against Senior level requirements

#### Scenario: Calculate gaps for different path

- **WHEN** collaborator enrolled in "Engineering Track" but requests gaps for "Management Track" level
- **THEN** system calculates gaps against Management Track requirements

### Requirement: Handle missing evaluation gracefully

The system SHALL provide meaningful response when no finalized evaluation exists for collaborator.

#### Scenario: No evaluation available

- **WHEN** collaborator has never completed an evaluation
- **THEN** system indicates gap analysis cannot be performed without baseline assessment

#### Scenario: Only draft evaluations exist

- **WHEN** collaborator has only RASCUNHO or CONCLUÍDA evaluations
- **THEN** system indicates awaiting finalized evaluation (ACEITA or CONTESTADA)

### Requirement: Include competency context in gaps

The system SHALL include complete competency information (name, category, group, level descriptions) in gap analysis results.

#### Scenario: Return gap with competency details

- **WHEN** system calculates gap for Python competency
- **THEN** result includes competency name, category "Technical Skills", group "Programming", and level descriptions

#### Scenario: Include both current and required levels

- **WHEN** gap analysis returns results
- **THEN** each gap shows current level from evaluation and required level from path

### Requirement: Calculate gaps without infrastructure dependencies

The system SHALL perform gap calculation as pure domain logic accepting domain entities as input, with no database queries or HTTP calls.

#### Scenario: Calculate from in-memory entities

- **WHEN** application provides Evaluation entity and PathLevel entity to gap service
- **THEN** service calculates gaps using only data in provided entities

#### Scenario: No external service calls during calculation

- **WHEN** gap analysis executes
- **THEN** system performs no database queries, API calls, or file system operations
