## Context

The loader currently reads the server name from the task YAML (`server: semantic`), then resolves it via `servers.yaml`. The `--server` CLI flag overrides this via `server_override`. This design requires every task file to carry a server name — a coupling that prevents reuse.

The change inverts control: the caller (CLI) always supplies the server name; the task file never carries it.

Current state (simplified):
```
task_file.yaml  ──► loader(path, server_override=None)  ──► suite["server"] resolved
                     ^-- reads data["server"] from YAML       from servers.yaml
```

Target state:
```
CLI: --server <name> (required)  ──► loader(path, server_name=<name>)  ──► suite["server"] resolved
task_file.yaml has NO server key         raises if server: found          from servers.yaml
```

Affected files: `probe/loader.py`, `probe/cli.py`, `examples/northwind/tasks/northwind.yaml`, `README.md`.

## Goals / Non-Goals

**Goals:**
- Task files contain only prompts and expectations — zero server coupling.
- `--server` is a required CLI argument on `eval` and `full`; errors show available server names.
- Task files with a legacy `server:` field get a clear, actionable error (not silently ignored).
- The servers.yaml format and lookup logic are unchanged.

**Non-Goals:**
- Changing how `--compare` works beyond validating against servers.yaml (it already does).
- Changing runner, scorer, reporter, judge, or config — they consume `suite["server"]` which remains the same resolved dict.
- Inferring the server from context (e.g., from the task directory) — server is always explicit.

## Decisions

### Decision: `server_name` is a required positional parameter, not optional

**Rationale**: Making it `str` (not `str | None`) in the function signature makes the contract explicit — callers must always supply a server name. The previous `server_override: str | None` with fallback to `data["server"]` was load-bearing; removing the fallback means the parameter is always used.

**Alternative considered**: Keep `server_override` optional and require it at the CLI level only. Rejected — it leaves a gap where `load_tasks()` can be called without a server name from Python code, which silently reads a non-existent field from the task YAML and errors in a confusing way.

### Decision: `server:` in a task file is an error, not a warning

**Rationale**: Silently ignoring the field would mask mistakes where a user edits a task file but forgets the server is now a CLI flag. A hard error ensures a single, clear upgrade path.

**Alternative considered**: UserWarning (like the legacy `expect` key deprecation). Rejected — the task would still fail to run (no server name is supplied to the loader), so a warning-then-failure sequence is worse than a single clear error.

### Decision: Error messages include the list of available servers

**Rationale**: "server 'foo' not found" without context forces the user to open `servers.yaml` manually. Including "Available: semantic, raw" in the message is the difference between a one-step and a two-step fix.

**Implementation**: `_resolve_server()` already builds this list. The `--server` required-but-missing case is handled by Click's built-in `UsageError`; we add a custom `invoke_without_command` callback or use `is_eager=False` combined with `required=True` so Click shows the missing-option error before any loader call is made.

### Decision: `--compare` does not become required; it stays optional

**Rationale**: `--compare` is an optional comparison mode. Adding it changes the eval to a dual-server run. Requiring it would change the primary usage of `eval`. The compare server is always validated against `servers.yaml` by the existing `_resolve_server` path.

## Risks / Trade-offs

- **[Risk] Breaking change for existing task files** → Anyone running `probe-mcp eval tasks/my.yaml` without `--server` will get a missing-option error. Mitigation: the error shows exactly what to add. All example files in the repo are updated in the same commit.
- **[Risk] CI scripts that use the old form break silently (exit 1, no explanation)** → Click prints a clear `Error: Missing option '--server'.` message to stderr before exiting. No silent failure.
- **[Risk] `load_tasks()` used programmatically without server name** → Type annotation (`server_name: str`, no default) makes this a static type error. Any caller that passed `server_override=None` or nothing must be updated.

## Migration Plan

1. Update `probe/loader.py` — rename param, remove task-file `server` read, add rejection.
2. Update `probe/cli.py` — make `--server` required, update templates and help.
3. Update `examples/northwind/tasks/northwind.yaml` — remove `server:` line.
4. Update `README.md` — add `--server` to all `eval`/`full` examples.
5. Update specs.

Rollback: revert the four changed files; the loader interface is internal to the CLI.

## Open Questions

_(none — scope is fully defined by the proposal)_
