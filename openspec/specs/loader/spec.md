# Spec: Loader

## Purpose

The loader module parses and validates a task YAML file, returning a task suite dict ready for the runner. It enforces structural and type constraints on every field and raises typed Python exceptions on any violation so the CLI can display a clean error message.

## Requirements

### Requirement: File must exist and be a YAML file

The loader SHALL raise `FileNotFoundError` if the given path does not exist, and `ValueError` if the file does not have a `.yaml` extension.

#### Scenario: Missing file raises FileNotFoundError

- **WHEN** `load_tasks("nonexistent.yaml")` is called with a path that does not exist
- **THEN** `FileNotFoundError` is raised with a message containing the path

#### Scenario: Non-YAML extension raises ValueError

- **WHEN** `load_tasks("tasks.json")` is called
- **THEN** `ValueError` is raised mentioning the wrong extension

---

### Requirement: Valid YAML content is required

The loader SHALL raise `ValueError` wrapping the YAML parser error if the file content is not valid YAML.

#### Scenario: Malformed YAML raises ValueError

- **WHEN** the file contains invalid YAML syntax
- **THEN** `ValueError` is raised with a message referencing the file path and the parse error

---

### Requirement: Top-level structure must be a mapping

The loader SHALL raise `ValueError` if the parsed YAML is not a Python `dict` (e.g. a bare list or scalar).

#### Scenario: Non-dict top level raises ValueError

- **WHEN** the YAML file contains a top-level list instead of a mapping
- **THEN** `ValueError` is raised indicating a mapping is required

---

### Requirement: server field is required and non-empty

The loader SHALL raise `ValueError` if the task file lacks a `server` key, or if `server` is not a non-empty string.

#### Scenario: Missing server key raises ValueError

- **WHEN** the YAML has no `server` key
- **THEN** `ValueError` is raised with a message referencing `server`

#### Scenario: Empty server string raises ValueError

- **WHEN** `server` is an empty string or whitespace-only
- **THEN** `ValueError` is raised

---

### Requirement: tasks field is a non-empty list

The loader SHALL raise `ValueError` if the task file lacks a `tasks` key, or if `tasks` is not a non-empty list.

#### Scenario: Missing tasks key raises ValueError

- **WHEN** the YAML has no `tasks` key
- **THEN** `ValueError` is raised with a message referencing `tasks`

#### Scenario: Empty tasks list raises ValueError

- **WHEN** `tasks` is an empty list `[]`
- **THEN** `ValueError` is raised

---

### Requirement: Each task must have a non-empty string id

The loader SHALL raise `ValueError` if any task is missing an `id` field or if the `id` is not a non-empty string.

#### Scenario: Missing id raises ValueError

- **WHEN** a task dict has no `id` key
- **THEN** `ValueError` is raised identifying the task position (e.g. `"Task #1"`)

#### Scenario: Non-string id raises ValueError

- **WHEN** a task `id` is an integer instead of a string
- **THEN** `ValueError` is raised

---

### Requirement: Duplicate task ids are rejected

The loader SHALL raise `ValueError` if any two tasks share the same `id`.

#### Scenario: Duplicate id raises ValueError

- **WHEN** two tasks both have `id: "same_id"`
- **THEN** `ValueError` is raised mentioning `"duplicate task id"`

---

### Requirement: Each task must have a non-empty string prompt

The loader SHALL raise `ValueError` if any task is missing a `prompt` field or if `prompt` is not a non-empty string.

#### Scenario: Missing prompt raises ValueError

- **WHEN** a task dict has no `prompt` key
- **THEN** `ValueError` is raised identifying the task by its id

---

### Requirement: Each task must have a dict expect field

The loader SHALL raise `ValueError` if any task is missing an `expect` field or if `expect` is not a dict.

#### Scenario: Missing expect raises ValueError

- **WHEN** a task dict has no `expect` key
- **THEN** `ValueError` is raised identifying the task by its id

---

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

If a task contains a top-level `trials` field (alongside `id`, `prompt`, and `expect`), the loader SHALL raise `ValueError` if it is not a positive integer greater than zero (booleans and floats are explicitly rejected). When absent, the effective default is `1`.

#### Scenario: Zero trials raises ValueError

- **WHEN** a task has `trials: 0`
- **THEN** `ValueError` is raised identifying the task by id

#### Scenario: Non-integer trials raises ValueError

- **WHEN** a task has `trials: 1.5`
- **THEN** `ValueError` is raised for that task

#### Scenario: Valid trials passes validation

- **WHEN** a task has `trials: 3`
- **THEN** the task loads successfully

#### Scenario: Absent trials defaults to 1

- **WHEN** a task has no `trials` key
- **THEN** the task loads successfully and the runner treats it as a single run

---

### Requirement: Flat expect keys emit a deprecation warning

If a task's `expect` dict contains any of the legacy flat keys (`tools_called_includes`, `max_calls`, `answer_includes`) at the top level — i.e., not nested under `deterministic` — the loader SHALL emit a `UserWarning` naming the task id and the offending keys. The file SHALL still load successfully (no error raised).

#### Scenario: Flat tools_called_includes emits warning

- **WHEN** a task's `expect` dict contains `tools_called_includes` at the top level (not under `deterministic`)
- **THEN** a `UserWarning` is emitted that names the task id and mentions `tools_called_includes`, and the suite is returned without error

#### Scenario: Multiple flat keys produce a single combined warning

- **WHEN** a task's `expect` dict contains both `max_calls` and `answer_includes` at the top level
- **THEN** a single `UserWarning` is emitted naming both keys for that task

---

### Requirement: Valid file returns complete task suite

When all validations pass the loader SHALL return the parsed dict containing at minimum the `server` string and the `tasks` list, each task preserving its `id`, `prompt`, and `expect`.

#### Scenario: Valid YAML returns parsed suite

- **WHEN** the task file contains a valid `server` and at least one task with `id`, `prompt`, and `expect`
- **THEN** `load_tasks()` returns a dict with `"server"` and `"tasks"` keys, and each task dict contains `"id"`, `"prompt"`, and `"expect"`
