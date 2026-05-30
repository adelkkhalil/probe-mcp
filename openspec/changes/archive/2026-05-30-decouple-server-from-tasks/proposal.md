## Why

Task files encode what to test (prompts and expectations); the server to test against is a runtime decision. Baking `server: semantic` into a task file makes the file only runnable against one server by default, defeating the purpose of eval-driven server comparison. Removing the `server` field enforces the clean separation that already exists architecturally.

## What Changes

- **BREAKING** `probe/loader.py` — the `server` field is forbidden in task files; the loader raises a clear error if it finds one. The `server_name` is now a required caller-supplied parameter instead of being read from the task YAML.
- **BREAKING** `probe/cli.py` — `--server` becomes a required option on `eval` and `full` commands (no default). `--compare` remains optional.
- `probe/cli.py` — missing `--server` on `eval`/`full` shows available server names from `servers.yaml` in the error message.
- `probe/cli.py` — `init` template (`_SAMPLE_TASKS`) removes the `server:` field; help command updates workflow examples.
- `examples/northwind/tasks/northwind.yaml` — `server: semantic` line removed.
- `openspec/specs/loader/spec.md` and `openspec/specs/cli/spec.md` — updated to match new requirements.
- `README.md` — all usage examples updated to include `--server`.

## Capabilities

### New Capabilities

_(none — this is a restructuring of existing behavior)_

### Modified Capabilities

- `loader`: The `server` requirement changes fundamentally — the loader no longer reads or validates a `server` field from the task YAML. Instead it accepts a required `server_name` parameter from the caller. Finding a `server:` field in a task file is now an error (not a valid input). The `Valid file returns complete task suite` requirement changes accordingly.
- `cli`: The `eval` and `full` commands change — `--server` goes from optional override to required argument. The error contract for missing/unknown server names becomes richer (shows available servers).

## Impact

- **`probe/loader.py`**: `load_tasks()` signature change — `server_override: str | None = None` → `server_name: str`; remove the `server` field read/validate block; add a rejection error for `server:` found in task file.
- **`probe/cli.py`**: `--server` option changed to `required=True` on `eval` and `full`; `_SAMPLE_TASKS` template updated; `help` command workflow updated.
- **`examples/northwind/tasks/northwind.yaml`**: `server: semantic` line removed.
- **`README.md`**: All `eval` and `full` usage examples updated to include `--server <name>`.
- **No changes**: `runner.py`, `scorer.py`, `reporter.py`, `judge.py`, `config.py`, `servers.yaml` format.
