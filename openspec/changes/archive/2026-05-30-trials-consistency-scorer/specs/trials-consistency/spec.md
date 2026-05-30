## ADDED Requirements

### Requirement: trials field is validated in the loader
The loader SHALL accept an optional `trials` field inside `expect.deterministic`. When present it MUST be a positive integer (> 0). Booleans and floats SHALL be rejected with `ValueError`. When absent, the default effective value is `1`.

#### Scenario: Valid trials passes validation
- **WHEN** `expect.deterministic.trials` is `3`
- **THEN** the task loads successfully with no warnings

#### Scenario: Zero trials raises ValueError
- **WHEN** `expect.deterministic.trials` is `0`
- **THEN** `ValueError` is raised identifying the task by id

#### Scenario: Float trials raises ValueError
- **WHEN** `expect.deterministic.trials` is `1.5`
- **THEN** `ValueError` is raised for that task

#### Scenario: Boolean trials raises ValueError
- **WHEN** `expect.deterministic.trials` is `true`
- **THEN** `ValueError` is raised for that task

#### Scenario: Absent trials defaults to 1
- **WHEN** a task's `expect.deterministic` has no `trials` key
- **THEN** the task loads successfully and runner treats trials as 1 (single run, unchanged behaviour)
