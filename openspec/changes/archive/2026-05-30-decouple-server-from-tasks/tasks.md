## 1. Loader Update

- [x] 1.1 In `probe/loader.py`, rename `server_override: str | None = None` to `server_name: str` in `load_tasks()` and remove the `server_override if server_override is not None else data["server"]` fallback line
- [x] 1.2 Remove the `"server" not in data` and `not isinstance(data["server"], str)` validation block (the `server` field is no longer read from the task YAML)
- [x] 1.3 Add a rejection block: if `"server"` in `data`, raise `ValueError("Task files no longer support a 'server' field. Remove it and pass the server name via --server.")`
- [x] 1.4 Add validation: if `server_name` is empty/whitespace, raise `ValueError`
- [x] 1.5 Update the `_resolve_server()` call to use `server_name` directly (the variable formerly called `server_name = server_override if ... else data["server"]`)

## 2. CLI Update

- [x] 2.1 In `probe/cli.py`, on the `eval` command, change `--server` from `default=None` / optional to `required=True` (remove `default`, add `required=True`)
- [x] 2.2 On the `full` command, apply the same change: `--server` becomes `required=True`
- [x] 2.3 Update `_SAMPLE_TASKS` template string — remove the `server: my_server` line and its comment, leaving only `tasks:`
- [x] 2.4 Update the `help` command workflow examples: change step 3 from `probe-mcp full tasks/my_server.yaml` to `probe-mcp full tasks/my_server.yaml --server my_server`

## 3. Example Files

- [x] 3.1 In `examples/northwind/tasks/northwind.yaml`, remove the `server: semantic` line (and the blank line after it if present)

## 4. README

- [x] 4.1 In `README.md`, find all `probe-mcp eval` and `probe-mcp full` usage examples and add `--server <server_name>` to each

## 5. Spec Update

- [x] 5.1 Update `openspec/specs/loader/spec.md` — apply the delta spec: remove the "server field is required and non-empty" requirement; add the "server field in task file is rejected" requirement; update "server_name is a required caller-supplied parameter" requirement; update "servers.yaml is loaded during suite parsing" and "Valid file returns complete task suite" requirements
- [x] 5.2 Update `openspec/specs/cli/spec.md` — apply the delta spec: replace the `eval --server overrides` requirement with the new `eval --server specifies the required server name` requirement; update `eval command` and `full command` requirements to show `--server` as required; update `init` requirement to show no `server:` field in generated tasks file

## 6. Verification

- [x] 6.1 Run `uv run python -m probe.cli eval examples/northwind/tasks/northwind.yaml --server semantic` and confirm it loads correctly (MCP session connects, tools listed — Anthropic API errors are pre-existing and not a regression)
- [x] 6.2 Run `uv run python -m probe.cli eval examples/northwind/tasks/northwind.yaml` (no `--server`) and confirm Click prints `Error: Missing option '--server'.`
- [x] 6.3 Run `uv run python -m probe.cli eval examples/northwind/tasks/northwind.yaml --server nonexistent` and confirm the error names the unknown server and lists available servers
