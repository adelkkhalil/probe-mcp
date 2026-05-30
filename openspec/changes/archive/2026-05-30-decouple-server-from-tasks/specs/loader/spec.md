## REMOVED Requirements

### Requirement: server field is required and non-empty

**Reason**: Task files no longer carry a server field — the server is a runtime argument supplied by the caller (CLI `--server`). Embedding a server name in a task file couples the tasks to a specific server, defeating the eval harness's goal of running the same tasks against multiple servers.

**Migration**: Remove the `server:` field from task files. Pass the server name via `--server <name>` on the CLI, or as the `server_name` argument to `load_tasks()`.

---

## ADDED Requirements

### Requirement: server field in task file is rejected with a clear error

If the task YAML contains a `server` key, the loader SHALL raise `ValueError` with the message: `Task files no longer support a 'server' field. Remove it and pass the server name via --server.`

#### Scenario: Task file with server field raises ValueError

- **WHEN** the task YAML contains `server: semantic` (or any server name)
- **THEN** `ValueError` is raised with a message telling the user to remove the field and use `--server`

---

### Requirement: server_name is a required caller-supplied parameter

`load_tasks()` SHALL accept a required `server_name: str` parameter (no default). The server name is resolved against `servers.yaml` using the existing two-step lookup. Callers MUST supply a non-empty server name; the loader SHALL raise `ValueError` if `server_name` is empty or whitespace.

#### Scenario: load_tasks resolves server_name from caller

- **WHEN** `load_tasks("tasks.yaml", server_name="semantic")` is called and `servers.yaml` defines `semantic`
- **THEN** `load_tasks()` succeeds and `suite["server"]` is the resolved dict for `semantic`

#### Scenario: Empty server_name raises ValueError

- **WHEN** `load_tasks("tasks.yaml", server_name="")` is called
- **THEN** `ValueError` is raised

---

## MODIFIED Requirements

### Requirement: servers.yaml is loaded during suite parsing

When `load_tasks()` is called, the loader SHALL locate `servers.yaml` using the two-step lookup (task file directory first, then task file parent directory, then `PROBE_CWD`), parse it, and resolve the caller-supplied `server_name` to the corresponding command/args dict. Errors from `servers.yaml` loading or name resolution SHALL propagate as `FileNotFoundError` or `ValueError` with clear messages. The error for an unknown server name SHALL list available server names.

#### Scenario: Matching servers.yaml resolves server_name

- **WHEN** `load_tasks("tasks/foo.yaml", server_name="semantic")` is called and `servers.yaml` in the task directory (or its parent, or `PROBE_CWD`) defines `semantic`
- **THEN** `load_tasks()` succeeds and `suite["server"]` is the resolved dict

#### Scenario: Missing servers.yaml raises FileNotFoundError

- **WHEN** no `servers.yaml` exists in the task directory, its parent, or `PROBE_CWD`
- **THEN** `FileNotFoundError` is raised with a message telling the user to create `servers.yaml` or run `probe-mcp init`

#### Scenario: Unknown server name raises ValueError with available names

- **WHEN** `server_name="unknown"` and `servers.yaml` has no such key
- **THEN** `ValueError` is raised naming the unresolved server name and listing the available server names from `servers.yaml`

---

### Requirement: Valid file returns complete task suite

When all validations pass the loader SHALL return the parsed dict containing at minimum the `server` config dict (resolved from `servers.yaml` using the caller-supplied `server_name`) and the `tasks` list, each task preserving its `id`, `prompt`, and `expect`. The `server` value in the returned suite SHALL be `{"name": str, "command": str, "args": list[str], "cwd": str}` — not the raw string from the YAML (the task YAML contains no `server` field).

#### Scenario: Valid YAML without server field returns parsed suite with resolved server config

- **WHEN** the task file contains only `tasks` (no `server` field), and `load_tasks("tasks.yaml", server_name="semantic")` is called with a name that resolves in `servers.yaml`
- **THEN** `load_tasks()` returns a dict where `suite["server"]` is `{"name": str, "command": str, "args": list[str], "cwd": str}` and `suite["tasks"]` contains each task
