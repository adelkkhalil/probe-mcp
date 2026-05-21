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

### Requirement: tools_called_includes must be a list of strings

If a task's `expect` contains `tools_called_includes`, the loader SHALL raise `ValueError` if it is not a list where every element is a string.

#### Scenario: Non-list tools_called_includes raises ValueError

- **WHEN** `expect.tools_called_includes` is a bare string instead of a list
- **THEN** `ValueError` is raised for that task

---

### Requirement: max_calls must be a non-negative integer

If a task's `expect` contains `max_calls`, the loader SHALL raise `ValueError` if it is not a non-negative integer (booleans are explicitly rejected).

#### Scenario: Negative max_calls raises ValueError

- **WHEN** `expect.max_calls` is `-1`
- **THEN** `ValueError` is raised for that task

#### Scenario: Boolean max_calls raises ValueError

- **WHEN** `expect.max_calls` is `true`
- **THEN** `ValueError` is raised for that task

---

### Requirement: answer_includes must be a string

If a task's `expect` contains `answer_includes`, the loader SHALL raise `ValueError` if it is not a string.

#### Scenario: Non-string answer_includes raises ValueError

- **WHEN** `expect.answer_includes` is a list
- **THEN** `ValueError` is raised for that task

---

### Requirement: Valid file returns complete task suite

When all validations pass the loader SHALL return the parsed dict containing at minimum the `server` string and the `tasks` list, each task preserving its `id`, `prompt`, and `expect`.

#### Scenario: Valid YAML returns parsed suite

- **WHEN** the task file contains a valid `server` and at least one task with `id`, `prompt`, and `expect`
- **THEN** `load_tasks()` returns a dict with `"server"` and `"tasks"` keys, and each task dict contains `"id"`, `"prompt"`, and `"expect"`
