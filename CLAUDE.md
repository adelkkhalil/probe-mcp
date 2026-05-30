# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

probe-mcp is an eval harness for MCP servers. It spawns an MCP server as a stdio subprocess, runs natural-language tasks through a real Anthropic API call with the server's tools attached, captures the tool-call trace, and scores results against per-task expectations. There is no mocking — the agent loop and the MCP protocol are both real.

The repo ships a reference example at `examples/northwind/` containing two MCP servers (`mcp_server_raw.py`, `mcp_server_semantic.py`), a legacy data API (`northwind_api.py` + `northwind.db`), a `servers.yaml`, and sample tasks. The two servers demonstrate how tool description quality changes agent behavior on the same underlying API — they are example targets for the harness, not part of it.

## Running things

This project uses **uv** (not pip). Python 3.12+ is required, plus an `ANTHROPIC_API_KEY` env var.

```bash
uv sync                                                    # install / refresh deps
uv run python -m probe.cli <command>                       # invoke the CLI
uv run python -m probe.cli eval examples/northwind/tasks/northwind.yaml
```

The `probe-mcp` console script is declared in `pyproject.toml` (`probe-mcp = "probe.cli:cli"`), so `uv run probe-mcp <command>` also works once the project is installed into the venv.

Common CLI commands (all live in `probe/cli.py`):

- `eval <tasks.yaml>` — run tasks against the server in the YAML, save results JSON
- `judge <results.json>` — run the LLM judge over a saved results file
- `full <tasks.yaml>` — eval + judge + report in one go
- `report <results.json>` — print results, auto-discovers a matching judge file via glob
- `eval --compare <server_name>` — runs the suite against two named servers and prints a side-by-side table
- `eval --server <server_name>` — override the server name from the task file

There are no tests in this repo. `ruff.toml` sets `line-length = 100`; format with `uv run ruff format` if needed.

## Architecture

The pipeline is a straight line: **loader → runner → scorer → reporter**, with **judge** as an optional second pass that reads the same saved results file.

```
tasks/*.yaml  ──►  loader  ──►  runner  ──►  results/*.json  ──►  scorer  ──►  reporter
                     │            │                                    ▲
                     ▼            ▼                                    │
               servers.yaml   MCP server subprocess                    │
               (resolved      (stdio, real protocol)                   │
                server name)                                           │
                                                                       │
                              results/*.json  ──►  judge  ──►  judge/*.json
```

Key cross-file contracts:

- **`probe/loader.py`** parses and validates the task YAML, then resolves `suite["server"]` from a named string to a `{"name", "command", "args", "cwd"}` dict via `servers.yaml`. It looks for `servers.yaml` in the task file's directory first, then `PROBE_CWD`. The loader accepts an optional `server_override` parameter to replace the server name before resolution (used by `--server` and `--compare` CLI flags). `suite["server"]` is always a dict after `load_tasks()` returns — never a bare string.

- **`probe/runner.py`** is the only piece that talks to the MCP protocol. It spawns the server via `StdioServerParameters(command=suite["server"]["command"], args=suite["server"]["args"], cwd=suite["server"]["cwd"])`, lists tools, then runs an agent loop: call `anthropic.messages.create` with the tool list, dispatch any `tool_use` blocks back through `session.call_tool`, append results, repeat until `end_turn`. The trace is a list of `{tool, params, error}` dicts. To suppress FastMCP banner/log noise it sets `FASTMCP_SHOW_SERVER_BANNER=false` and `FASTMCP_LOG_LEVEL=WARNING` unless `--verbose` is passed. The results filename stem uses `suite["server"]["name"]` (the named server key), not a file path.

- **`probe/scorer.py`** does *structural* pass/fail only. It supports three expectation keys: `tools_called_includes`, `max_calls`, `answer_includes` (case-insensitive). If `answer` starts with `"ERROR:"` it returns FAIL early with the parsed error message — that prefix is the contract the runner uses to signal an API/transport failure.

- **`probe/judge.py`** does *semantic* pass/fail. It loads `probe/judge_prompt.txt` (an external template, not an inline string) and validates that the required placeholders `{task_prompt}`, `{tool_trace}`, `{answer}` and the required output fields `"verdict"`, `"reason"` are present before use. The judge model returns JSON; verdicts outside `{PASS, PARTIAL, FAIL, ERROR}` are coerced to `ERROR`. If you edit the prompt, keep those placeholders/fields and bump the `prompt_version:` comment — it gets parsed and stored in the judge file's `meta`.

- **`probe/config.py`** loads `probe.yaml` with shallow per-key overrides on top of hardcoded defaults — missing keys fall back, missing file falls back entirely. Always read config via `get_agent_model` / `get_judge_model` / `get_results_dir` / `get_judge_dir`, not by indexing the dict directly.

- **File naming is part of the contract.** Results files are `{server_name}_{timestamp}_{model}_{run_id}.json` where `server_name` is the key from `servers.yaml`; judge files are `{results_stem}_judge_{judge_model}_{run_id}.json`. The `report` command finds a results file's judge by globbing `{results_stem}_judge_*.json` and picking the most recent by mtime — don't rename files by hand or this breaks. The model name in every filename always reflects the actual model used, never a placeholder.

## Things to keep consistent when changing code

- The runner's `"ERROR:"` answer prefix is load-bearing — scorer/reporter both special-case it. If you change the marker, update both.
- New expectation keys must be added in `probe/scorer.py` *and* documented in the `--help` output / README expectations list.
- `eval --compare` and `full --compare` call `load_tasks(tasks_file, server_override=compare)` to get the second suite independently — they do NOT deep-copy and mutate suite1. This ensures each suite has fully resolved server config for its respective server.
- The judge prompt's required-placeholder check is enforced at load time, not at format time. If you add a new variable to the prompt, update both `REQUIRED_PLACEHOLDERS` and the `judge_task` call site.
- `suite["server"]` is always a dict `{"name", "command", "args", "cwd"}` after `load_tasks()` returns. Code that reads `suite["server"]` must use the appropriate key — use `["name"]` for display/filenames, `["command"]`/`["args"]`/`["cwd"]` for spawning.

## Reference servers and target API

`examples/northwind/mcp_server_raw.py` and `examples/northwind/mcp_server_semantic.py` both import the same six functions from `northwind_api.py` (which is plain SQLite, no MCP). The "raw" server is intentionally a naive 1:1 wrapper with terse docstrings; the "semantic" one adds rich descriptions, parameter notes, a `limit` cap on `orders()`, and a composite `order_with_details` tool. Treat `northwind_api.py` as the "untouchable legacy API" it's modeled on — the point of the demo is that you can only change the MCP layer, not the underlying data access.

`examples/northwind/servers.yaml` defines `semantic` and `raw` server entries, each using `uv run --directory . python <script>` so the northwind project's own venv is used. `examples/northwind/pyproject.toml` declares the northwind project's dependencies (`fastmcp>=3.0.0`) so `uv run` works from that directory.
