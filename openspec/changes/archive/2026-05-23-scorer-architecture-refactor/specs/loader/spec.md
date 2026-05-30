## MODIFIED Requirements

### Requirement: tools_called_includes must be a list of strings

If a task's `expect.deterministic` contains `tools_called_includes`, the loader SHALL raise `ValueError` if it is not a list where every element is a string.

#### Scenario: Non-list tools_called_includes raises ValueError

- **WHEN** `expect.deterministic.tools_called_includes` is a bare string instead of a list
- **THEN** `ValueError` is raised for that task

---

### Requirement: max_calls must be a non-negative integer

If a task's `expect.deterministic` contains `max_calls`, the loader SHALL raise `ValueError` if it is not a non-negative integer (booleans are explicitly rejected).

#### Scenario: Negative max_calls raises ValueError

- **WHEN** `expect.deterministic.max_calls` is `-1`
- **THEN** `ValueError` is raised for that task

#### Scenario: Boolean max_calls raises ValueError

- **WHEN** `expect.deterministic.max_calls` is `true`
- **THEN** `ValueError` is raised for that task

---

### Requirement: answer_includes must be a string

If a task's `expect.deterministic` contains `answer_includes`, the loader SHALL raise `ValueError` if it is not a string.

#### Scenario: Non-string answer_includes raises ValueError

- **WHEN** `expect.deterministic.answer_includes` is a list
- **THEN** `ValueError` is raised for that task

---

## ADDED Requirements

### Requirement: expect.deterministic must be a dict when present

If a task's `expect` contains a `deterministic` key, the loader SHALL raise `ValueError` if its value is not a dict.

#### Scenario: Non-dict deterministic raises ValueError

- **WHEN** `expect.deterministic` is a list instead of a dict
- **THEN** `ValueError` is raised for that task identifying the field

---

### Requirement: expect.probabilistic must be a dict when present

If a task's `expect` contains a `probabilistic` key, the loader SHALL raise `ValueError` if its value is not a dict.

#### Scenario: Non-dict probabilistic raises ValueError

- **WHEN** `expect.probabilistic` is a string instead of a dict
- **THEN** `ValueError` is raised for that task identifying the field

---

### Requirement: probabilistic.judge must be a boolean when present

If a task's `expect.probabilistic` contains a `judge` key, the loader SHALL raise `ValueError` if its value is not a boolean.

#### Scenario: Non-boolean judge raises ValueError

- **WHEN** `expect.probabilistic.judge` is the string `"true"` instead of boolean `true`
- **THEN** `ValueError` is raised for that task

---

### Requirement: Flat expect keys emit a deprecation warning

If a task's `expect` dict contains any of the legacy flat keys (`tools_called_includes`, `max_calls`, `answer_includes`) at the top level — i.e., not nested under `deterministic` — the loader SHALL emit a `UserWarning` naming the task id and the offending keys. The file SHALL still load successfully (no error raised).

#### Scenario: Flat tools_called_includes emits warning

- **WHEN** a task's `expect` dict contains `tools_called_includes` at the top level (not under `deterministic`)
- **THEN** a `UserWarning` is emitted that names the task id and mentions `tools_called_includes`, and the suite is returned without error

#### Scenario: Multiple flat keys produce a single combined warning

- **WHEN** a task's `expect` dict contains both `max_calls` and `answer_includes` at the top level
- **THEN** a single `UserWarning` is emitted naming both keys for that task
