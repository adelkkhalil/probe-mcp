## MODIFIED Requirements

### Requirement: server field is required and non-empty

The loader SHALL raise `ValueError` if the task file lacks a `server` key, or if `server` is not a non-empty string. The value is treated as a server name to be resolved against `servers.yaml` — it is not interpreted as a file path.

#### Scenario: Missing server key raises ValueError

- **WHEN** the YAML has no `server` key
- **THEN** `ValueError` is raised with a message referencing `server`

#### Scenario: Empty server string raises ValueError

- **WHEN** `server` is an empty string or whitespace-only
- **THEN** `ValueError` is raised

---

### Requirement: Valid file returns complete task suite

When all validations pass the loader SHALL return the parsed dict containing at minimum the `server` config dict (resolved from `servers.yaml`) and the `tasks` list, each task preserving its `id`, `prompt`, and `expect`. The `server` value in the returned suite SHALL be `{"command": str, "args": list[str], "cwd": str}` — not the raw string from the YAML.

#### Scenario: Valid YAML returns parsed suite with resolved server config

- **WHEN** the task file contains a valid `server` name that resolves in `servers.yaml`, and at least one task with `id`, `prompt`, and `expect`
- **THEN** `load_tasks()` returns a dict where `suite["server"]` is `{"command": str, "args": list[str], "cwd": str}` and `suite["tasks"]` contains each task

## ADDED Requirements

### Requirement: servers.yaml is loaded during suite parsing

When `load_tasks()` is called, the loader SHALL locate `servers.yaml` using the two-step lookup defined in the `server-config` spec (task file directory first, then `PROBE_CWD`), parse it, and resolve `suite["server"]` from the server name in the task YAML to the corresponding command/args dict. Errors from `servers.yaml` loading or name resolution SHALL propagate as `FileNotFoundError` or `ValueError` with clear messages.

#### Scenario: Matching servers.yaml resolves server name

- **WHEN** the task file has `server: semantic` and `servers.yaml` in the same directory defines `semantic`
- **THEN** `load_tasks()` succeeds and `suite["server"]` is the resolved dict

#### Scenario: Missing servers.yaml raises FileNotFoundError

- **WHEN** no `servers.yaml` exists in the task directory or `PROBE_CWD`
- **THEN** `FileNotFoundError` is raised before the suite is returned

#### Scenario: Unknown server name raises ValueError

- **WHEN** the task file specifies `server: unknown` and `servers.yaml` has no such key
- **THEN** `ValueError` is raised naming the unresolved server name
