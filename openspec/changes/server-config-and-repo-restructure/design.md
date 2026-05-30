## Context

The harness currently spawns every MCP server via `StdioServerParameters(sys.executable, [server_path])`. Because it always uses probe-mcp's own Python interpreter, any target server that needs a different environment (different package versions, a non-Python runtime, a wrapper script) cannot be evaluated. Separately, the repo root mixes framework source (`probe/`) with user-generated artifacts (`probe.yaml`, `tasks/`, `results/`, `judge/`) and a bundled example (`mcp_server_*.py`, `northwind_api.py`, `northwind.db`), making it hard to understand what is "the harness" vs. "an example" vs. "my data."

## Goals / Non-Goals

**Goals:**
- Allow any server command/args to be used — not just `python <file>`.
- Move subprocess configuration out of task YAMLs and into a dedicated `servers.yaml` file.
- Cleanly separate framework source from the northwind example.
- Remove user-generated output files from git.
- Remove `--ignore-tool-names` now that it has no remaining use case.

**Non-Goals:**
- Supporting non-stdio transports (SSE, HTTP).
- Dynamic server installation or venv creation.
- Backward compatibility with the old file-path `server:` field.

## Decisions

### Decision: servers.yaml lives alongside the task file, not globally

**Chosen**: The loader looks for `servers.yaml` in the task file's directory first, then falls back to `PROBE_CWD`. The runner receives the resolved `{command, args}` dict — it never reads `servers.yaml` directly.

**Why over a global config**: A global `probe.yaml` `servers:` section would entangle server definitions with eval configuration. A per-project `servers.yaml` lets different task directories reference different server registries, matching how real projects are structured (each repo has its own server).

**Why over inline command in task YAML**: Centralising command/args in `servers.yaml` means multiple task files can reference the same server definition by name. It also avoids exposing shell-level concerns in every task file.

---

### Decision: Loader resolves the server name; runner receives a dict

**Chosen**: `load_tasks()` returns a suite where `suite["server"]` is replaced with a `{"command": str, "args": list[str]}` dict. The runner only consumes the dict — it has no knowledge of `servers.yaml`.

**Why**: Keeps the runner focused on the MCP protocol. All path lookup, YAML parsing, and error reporting for server resolution belong in the loader alongside the task-file parsing that already happens there.

---

### Decision: subprocess cwd is set to the servers.yaml directory

**Chosen**: `StdioServerParameters` does not support a `cwd` argument, so the runner passes `cwd` to the underlying asyncio subprocess by wrapping the call site. The cwd is the directory that contained `servers.yaml`.

**Why**: Relative paths in `args` (e.g. `["run", "--directory", ".", "python", "mcp_server.py"]`) must resolve relative to the project root, not the directory where the user ran `probe-mcp`. Setting cwd to the `servers.yaml` directory makes this deterministic.

---

### Decision: --ignore-tool-names is removed entirely

**Why**: Its only purpose was to strip `tools_called_includes` from task expectations when comparing servers with different tool names. Since server comparison now uses explicit per-task YAML expectations, the flag has no remaining use and its removal simplifies the CLI surface.

---

### Decision: Northwind moves to examples/northwind/, root-level artifacts deleted

**Chosen**: `examples/northwind/` becomes a self-contained project: servers.yaml, probe.yaml, tasks/, and all server/data files. The repo root no longer contains user-generated directories.

**Why over keeping them at root**: The root mixing framework and example content caused confusion — new users couldn't tell what was required vs. illustrative. Moving the example out also makes the framework's git history cleaner (no results/ churn).

**Gitignore strategy**: `probe.yaml`, `servers.yaml`, `results/`, `judge/` are added to `.gitignore` so that users who run `probe-mcp init` in any directory don't accidentally commit their workspace. The northwind example is explicitly un-ignored via `!examples/northwind/**`.

---

### Decision: init creates both probe.yaml and servers.yaml

**Why**: After this change, `servers.yaml` is equally essential to getting started. Generating only `probe.yaml` would leave new users with no way to run the sample task. Both files are created idempotently (skip if exists, overwrite with `--force`).

## Risks / Trade-offs

- **Existing task YAMLs break** — any `server: mcp_server_semantic.py` field is now an invalid server name. There is no migration path; users must update their files. Acceptable given the explicit "clean break" intent.
- **servers.yaml lookup order is implicit** — task-dir-first then PROBE_CWD could be surprising. Mitigation: the loader prints the resolved path in verbose mode and raises a clear error naming both locations it searched.
- **cwd injection via asyncio subprocess wrapper** — `mcp` library's `StdioServerParameters` does not expose `cwd`. Mitigation: wrap the spawning call to inject `cwd` into the asyncio `create_subprocess_exec` call, or shell out via a thin wrapper script. Confirm approach at implementation time based on library internals.
- **examples/ gitignore pattern** — `examples/*/` ignores all non-northwind example directories. If someone contributes a second example, they'll need to add an explicit un-ignore pattern. Acceptable trade-off for keeping the repo clean.

## Migration Plan

1. Create `examples/northwind/` directory structure.
2. Move northwind files and tasks; create `examples/northwind/servers.yaml`.
3. Update `probe/loader.py` to load `servers.yaml` and resolve server names.
4. Update `probe/runner.py` to use `command`/`args` dict and set `cwd`.
5. Update `probe/cli.py`: remove `--ignore-tool-names`, update `--server`/`--compare` help text, update `init`, update `status`.
6. Update `.gitignore` and `README.md`.
7. Delete root-level user artifacts (`probe.yaml`, `tasks/`, `results/`, `judge/`, northwind files).

No rollback strategy — this is a clean break with no parallel support for the old format.

## Open Questions

- Can `mcp` library's `StdioServerParameters` accept a `cwd` parameter, or does the runner need to patch `asyncio.create_subprocess_exec` after the fact? Needs a quick check of library internals before implementation.
