## 1. Repo Restructure

- [x] 1.1 Create `examples/northwind/` directory and move `mcp_server_raw.py`, `mcp_server_semantic.py`, `northwind_api.py`, `northwind.db` into it
- [x] 1.2 Create `examples/northwind/tasks/` and move `tasks/northwind.yaml` there
- [x] 1.3 Move root-level `probe.yaml` to `examples/northwind/probe.yaml`
- [x] 1.4a Add `examples/northwind/pyproject.toml` with minimal uv project content so `uv run --directory .` works from that directory
- [x] 1.4 Create `examples/northwind/servers.yaml` with `semantic` and `raw` server entries using `uv run` commands
- [x] 1.5 Delete root-level `tasks/`, `results/`, `judge/` directories (after moving contents)
- [x] 1.6 Update `.gitignore` to exclude `probe.yaml`, `servers.yaml`, `results/`, `judge/`, `*.log`, and non-northwind examples

## 2. Loader — servers.yaml Resolution

- [x] 2.1 Add `load_servers(task_file_path)` function in `probe/loader.py` that implements the two-step lookup (task-dir → PROBE_CWD) and raises `FileNotFoundError` if not found
- [x] 2.2 Parse `servers.yaml` content; validate top-level `servers` mapping is non-empty and each entry has a non-empty `command` string and a `args` list of strings; raise `ValueError` on violations
- [x] 2.3 Add `resolve_server(name, servers_yaml_path)` that looks up the name and returns `{"command", "args", "cwd"}`; raises `ValueError` if the name is not found
- [x] 2.4 Modify `load_tasks()` to call `load_servers()` + `resolve_server()` after parsing the task YAML, and replace `suite["server"]` with the resolved dict before returning
- [x] 2.5 Update the `server field is required and non-empty` validation comment/docstring to clarify the value is a server name, not a file path

## 3. Runner — subprocess Command/Args

- [x] 3.1 Check `mcp` library's `StdioServerParameters` for a `cwd` parameter; if absent, identify how to inject `cwd` into the asyncio subprocess call (patch site or wrapper)
- [x] 3.2 Replace `StdioServerParameters(command=sys.executable, args=[server_path])` with `StdioServerParameters(command=suite["server"]["command"], args=suite["server"]["args"])` and set `cwd=suite["server"]["cwd"]`
- [x] 3.3 Remove any `sys.executable` import/usage that was only needed for the old spawn path

## 4. CLI — Flag Changes

- [x] 4.1 Update `--server` option help text on `eval` and `full` to say "server name (from servers.yaml)" instead of referencing a file path
- [x] 4.2 Update `--compare` option help text on `eval` and `full` similarly
- [x] 4.3 Remove `--ignore-tool-names` option from `eval` and `full` commands and delete the stripping logic

## 5. CLI — init Command

- [x] 5.1 Add `servers.yaml` to the set of files `init` creates, with a commented example server entry
- [x] 5.2 Update the sample `tasks/my_server.yaml` template to use `server: my_server` (a name, not a path)
- [x] 5.3 Ensure `init` prints a confirmation (or skip/overwrite message) for `servers.yaml` alongside the existing messages

## 6. CLI — status Command

- [x] 6.1 Add a Servers section to `status` output: locate `servers.yaml` via the same two-step lookup, render each named server's command and args in a Rich table
- [x] 6.2 When `servers.yaml` is absent, print a "no servers configured — run `probe-mcp init`" message in the Servers section instead of raising an error

## 7. README and CLAUDE.md

- [x] 7.1 Update `README.md` to document the new `servers.yaml` format, the named-server workflow, and the `examples/northwind/` layout
- [x] 7.2 Update `CLAUDE.md` to reflect the new loader contract (`suite["server"]` is now a dict), runner spawn changes, and the removal of `--ignore-tool-names`
- [x] 7.3 Update any README quick-start commands that reference root-level task files or old `--server path.py` syntax
