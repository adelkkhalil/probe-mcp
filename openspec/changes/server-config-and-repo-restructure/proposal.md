## Why

The harness currently spawns MCP servers using `sys.executable`, which locks every target server into probe-mcp's own venv — making it impossible to eval servers with different dependencies. The repo root also mixes framework code with example files (northwind servers, tasks, results, probe.yaml), which creates confusion for new users and pollutes the framework's git history with user-generated output.

## What Changes

- **BREAKING** `server:` in task files changes from a file path to a named server key resolved via `servers.yaml`.
- **BREAKING** `--server` and `--compare` CLI flags now accept a server name (from `servers.yaml`), not a file path.
- **BREAKING** `--ignore-tool-names` flag removed; each task YAML controls its own expectations directly.
- New `servers.yaml` format defines named servers with arbitrary `command` + `args` — the subprocess is spawned exactly as specified, enabling any venv, binary, or runtime.
- Loader gains responsibility for finding and parsing `servers.yaml` (task-file directory first, then `PROBE_CWD`), resolving server names, and raising clear errors when resolution fails.
- Runner switches from `StdioServerParameters(sys.executable, [path])` to `StdioServerParameters(command, args)` with the subprocess `cwd` set to the `servers.yaml` directory.
- Repo restructured: all northwind files move to `examples/northwind/`, including a new `examples/northwind/servers.yaml`. Root-level user artifacts (`probe.yaml`, `tasks/`, `results/`, `judge/`) are deleted.
- `probe-mcp init` now creates both `probe.yaml` and `servers.yaml` with example content.
- `probe-mcp status` surfaces servers defined in `servers.yaml`.
- `.gitignore` updated to exclude user-generated files and non-northwind examples.

## Capabilities

### New Capabilities

- `server-config`: Named server registry via `servers.yaml` — format definition, resolution logic (lookup order, path relativisation), and subprocess invocation contract.

### Modified Capabilities

- `loader`: Now resolves a server name through `servers.yaml` instead of accepting a bare file path; raises structured errors for missing file or unknown server name.
- `runner`: Spawns subprocess from `command`/`args` dict (not `sys.executable` + path); sets `cwd` to `servers.yaml` directory.
- `cli`: `--server`/`--compare` accept names; `--ignore-tool-names` removed; `init` creates `servers.yaml`; `status` lists servers.

## Impact

- `probe/loader.py` — add `servers.yaml` loading and server-name resolution
- `probe/runner.py` — change subprocess spawn call, add `cwd` parameter
- `probe/cli.py` — flag changes, `init` template update, `status` output update
- `examples/northwind/` — new directory receives all northwind files + `servers.yaml`
- `.gitignore` — expanded to exclude user artifacts and generated outputs
- `README.md` — updated to reflect new structure and `servers.yaml` workflow
- Existing `openspec/specs/` for `runner`, `loader`, `cli` — delta specs needed
