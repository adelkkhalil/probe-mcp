## ADDED Requirements

### Requirement: Results table shows consistency score when any task used trials

When any scored result in the list contains a `consistency_score` field, `print_results` SHALL add a `Consistency` column to the results table. For tasks with `consistency_score`, the cell shows the score as a percentage (e.g., `100%`, `67%`). For tasks without a `consistency_score`, the cell shows `—`.

#### Scenario: Consistency column appears when at least one task has trials

- **WHEN** at least one scored result has a `consistency_score` field
- **THEN** the results table includes a `Consistency` column

#### Scenario: Perfect consistency renders as 100%

- **WHEN** a scored result has `consistency_score: 1.0`
- **THEN** the Consistency cell shows `100%` in bold green

#### Scenario: Partial consistency renders in yellow

- **WHEN** a scored result has `consistency_score: 0.67`
- **THEN** the Consistency cell shows `67%` in bold yellow

#### Scenario: Zero consistency renders in red

- **WHEN** a scored result has `consistency_score: 0.0`
- **THEN** the Consistency cell shows `0%` in bold red

#### Scenario: Task without trials shows dash in consistency column

- **WHEN** a scored result has no `consistency_score` field and the table includes a Consistency column
- **THEN** the Consistency cell for that task shows `—`
