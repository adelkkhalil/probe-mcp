## ADDED Requirements

### Requirement: tools_called_excludes must be a list of strings

If a task's `expect.deterministic` contains `tools_called_excludes`, the loader SHALL raise `ValueError` if it is not a list where every element is a string.

#### Scenario: Non-list tools_called_excludes raises ValueError

- **WHEN** `expect.deterministic.tools_called_excludes` is a bare string
- **THEN** `ValueError` is raised for that task

#### Scenario: List with non-string element raises ValueError

- **WHEN** `expect.deterministic.tools_called_excludes` is `[123]`
- **THEN** `ValueError` is raised for that task

---

### Requirement: tool_called_count must be a non-negative integer

If a task's `expect.deterministic` contains `tool_called_count`, the loader SHALL raise `ValueError` if it is not a non-negative integer (booleans are explicitly rejected).

#### Scenario: Non-integer tool_called_count raises ValueError

- **WHEN** `expect.deterministic.tool_called_count` is `"one"`
- **THEN** `ValueError` is raised for that task

#### Scenario: Boolean tool_called_count raises ValueError

- **WHEN** `expect.deterministic.tool_called_count` is `true`
- **THEN** `ValueError` is raised for that task

#### Scenario: Negative tool_called_count raises ValueError

- **WHEN** `expect.deterministic.tool_called_count` is `-1`
- **THEN** `ValueError` is raised for that task

---

### Requirement: tool_params_include must be a dict with tool string and params list

If a task's `expect.deterministic` contains `tool_params_include`, the loader SHALL raise `ValueError` if it is not a dict, if `tool` is missing or not a non-empty string, or if `params` is missing or not a list of strings.

#### Scenario: Non-dict tool_params_include raises ValueError

- **WHEN** `expect.deterministic.tool_params_include` is a string
- **THEN** `ValueError` is raised for that task

#### Scenario: Missing tool key raises ValueError

- **WHEN** `expect.deterministic.tool_params_include` is `{"params": ["iban"]}` with no `tool` key
- **THEN** `ValueError` is raised for that task

#### Scenario: Non-list params raises ValueError

- **WHEN** `expect.deterministic.tool_params_include.params` is a bare string
- **THEN** `ValueError` is raised for that task

---

### Requirement: answer_excludes must be a string

If a task's `expect.deterministic` contains `answer_excludes`, the loader SHALL raise `ValueError` if it is not a string.

#### Scenario: Non-string answer_excludes raises ValueError

- **WHEN** `expect.deterministic.answer_excludes` is a list
- **THEN** `ValueError` is raised for that task

---

### Requirement: no_error must be the boolean true

If a task's `expect.deterministic` contains `no_error`, the loader SHALL raise `ValueError` if it is not the boolean `true`.

#### Scenario: Non-boolean no_error raises ValueError

- **WHEN** `expect.deterministic.no_error` is the string `"true"`
- **THEN** `ValueError` is raised for that task

#### Scenario: Boolean false no_error raises ValueError

- **WHEN** `expect.deterministic.no_error` is `false`
- **THEN** `ValueError` is raised for that task (only `true` is a meaningful value)

---

### Requirement: tools_called_sequence must be a list of strings

If a task's `expect.deterministic` contains `tools_called_sequence`, the loader SHALL raise `ValueError` if it is not a list where every element is a string.

#### Scenario: Non-list tools_called_sequence raises ValueError

- **WHEN** `expect.deterministic.tools_called_sequence` is a bare string
- **THEN** `ValueError` is raised for that task

---

### Requirement: trials must be a positive integer when present

If a task's `expect.deterministic` contains `trials`, the loader SHALL raise `ValueError` if it is not a positive integer greater than zero (booleans and floats are explicitly rejected).

#### Scenario: Zero trials raises ValueError

- **WHEN** `expect.deterministic.trials` is `0`
- **THEN** `ValueError` is raised for that task

#### Scenario: Non-integer trials raises ValueError

- **WHEN** `expect.deterministic.trials` is `1.5`
- **THEN** `ValueError` is raised for that task

#### Scenario: Valid trials passes validation

- **WHEN** `expect.deterministic.trials` is `3`
- **THEN** the task loads successfully
