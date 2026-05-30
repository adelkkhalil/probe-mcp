## ADDED Requirements

### Requirement: servers.yaml defines named server entries

A `servers.yaml` file SHALL contain a top-level `servers` mapping where each key is a server name (a non-empty string) and each value is a dict with a required `command` field (non-empty string) and a required `args` field (list of strings, may be empty).

#### Scenario: Valid servers.yaml is parsed correctly

- **WHEN** `servers.yaml` contains a `servers` mapping with at least one entry that has `command` and `args`
- **THEN** each server name resolves to `{"command": str, "args": list[str]}`

#### Scenario: Missing command field raises ValueError

- **WHEN** a server entry in `servers.yaml` omits the `command` key
- **THEN** `ValueError` is raised naming the server and the missing field

#### Scenario: Non-list args raises ValueError

- **WHEN** a server entry in `servers.yaml` has `args` set to a string instead of a list
- **THEN** `ValueError` is raised naming the server and the field

#### Scenario: Empty servers mapping raises ValueError

- **WHEN** `servers.yaml` contains `servers: {}` (an empty mapping)
- **THEN** `ValueError` is raised indicating no servers are defined

---

### Requirement: servers.yaml is located by a two-step lookup

The loader SHALL first look for `servers.yaml` in the same directory as the task file. If not found there, it SHALL look in the `PROBE_CWD` directory (or the process working directory if `PROBE_CWD` is not set). If neither location contains `servers.yaml`, the loader SHALL raise `FileNotFoundError` with a message naming both paths that were searched.

#### Scenario: servers.yaml found in task file directory

- **WHEN** `servers.yaml` exists in the same directory as the task file
- **THEN** it is used for server name resolution regardless of whether one also exists in `PROBE_CWD`

#### Scenario: servers.yaml found in PROBE_CWD when absent from task directory

- **WHEN** no `servers.yaml` exists in the task file directory but one exists in `PROBE_CWD`
- **THEN** the `PROBE_CWD` copy is used for resolution

#### Scenario: No servers.yaml found raises FileNotFoundError

- **WHEN** `servers.yaml` is absent from both the task file directory and `PROBE_CWD`
- **THEN** `FileNotFoundError` is raised with a message listing both paths that were searched

---

### Requirement: Server name is resolved to a command/args dict

Given a server name string, the loader SHALL look it up in the parsed `servers.yaml` and return a dict `{"command": str, "args": list[str], "cwd": str}` where `cwd` is the absolute path of the directory containing `servers.yaml`. If the name is not found, the loader SHALL raise `ValueError` naming the missing server and the `servers.yaml` path that was consulted.

#### Scenario: Known server name resolves to dict

- **WHEN** `suite["server"]` is `"semantic"` and `servers.yaml` defines a `semantic` entry
- **THEN** the loader returns `{"command": "uv", "args": [...], "cwd": "/path/to/servers.yaml/dir"}`

#### Scenario: Unknown server name raises ValueError

- **WHEN** `suite["server"]` is `"nonexistent"` and `servers.yaml` does not contain that key
- **THEN** `ValueError` is raised naming `"nonexistent"` and the `servers.yaml` path consulted

---

### Requirement: Runner spawns subprocess using the resolved server config

The runner SHALL call `StdioServerParameters` (or equivalent) with `command` and `args` from the resolved server dict, and SHALL set the subprocess working directory to `cwd` from that dict.

#### Scenario: Subprocess is launched with resolved command and args

- **WHEN** the resolved server dict is `{"command": "uv", "args": ["run", "python", "server.py"], "cwd": "/project"}`
- **THEN** the subprocess is spawned with `command="uv"`, `args=["run", "python", "server.py"]`, and `cwd="/project"`
