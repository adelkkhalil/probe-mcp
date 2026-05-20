# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

probe-mcp is an eval harness for MCP servers. It spawns an MCP server as a stdio subprocess, runs natural-language tasks through a real Anthropic API call with the server's tools attached, captures the tool-call trace, and scores results against per-task expectations. There is no mocking — the agent loop and the MCP protocol are both real.

The repo also ships two reference MCP servers (`mcp_server_raw.py`, `mcp_server_semantic.py`) and a small legacy data API (`northwind_api.py` + `northwind.db`) that they both wrap. The two servers exist to demonstrate how tool description quality changes agent behavior on the same underlying calls — they are example targets for the harness, not part of it.

## Running things

This project uses **uv** (not pip). Python 3.12+ is required, plus an `ANTHROPIC_API_KEY` env var.

```bash
uv sync                                # install / refresh deps
uv run python -m probe.cli <command>   # invoke the CLI
uv run python mcp_server_semantic.py   # run a target MCP server directly
```

The `probe-mcp` console script is declared in `pyproject.toml` (`probe-mcp = "probe.cli:cli"`), so `uv run probe-mcp <command>` also works once the project is installed into the venv.

Common CLI commands (all live in `probe/cli.py`):

- `eval <tasks.yaml>` — run tasks against the server in the YAML, save results JSON
- `judge <results.json>` — run the LLM judge over a saved results file
- `full <tasks.yaml>` — eval + judge + report in one go
- `report <results.json>` — print results, auto-discovers a matching judge file via glob
- `eval --compare <other_server.py>` — runs the suite against two servers and prints a side-by-side table
- `--ignore-tool-names` strips `tools_called_includes` from expectations at runtime (useful when comparing servers whose tools have different names)

There are no tests in this repo. `ruff.toml` sets `line-length = 100`; format with `uv run ruff format` if needed.

## Architecture

The pipeline is a straight line: **loader → runner → scorer → reporter**, with **judge** as an optional second pass that reads the same saved results file.

```
tasks/*.yaml  ──►  loader  ──►  runner  ──►  results/*.json  ──►  scorer  ──►  reporter
                                  │                                    ▲
                                  ▼                                    │
                          MCP server subprocess                        │
                          (stdio, real protocol)                       │
                                                                       │
                              results/*.json  ──►  judge  ──►  judge/*.json
```

Key cross-file contracts:

- **`probe/runner.py`** is the only piece that talks to the MCP protocol. It spawns the server via `StdioServerParameters(command=sys.executable, args=[server_path])`, lists tools, then runs an agent loop: call `anthropic.messages.create` with the tool list, dispatch any `tool_use` blocks back through `session.call_tool`, append results, repeat until `end_turn`. The trace is a list of `{tool, params}` dicts. To suppress FastMCP banner/log noise it sets `FASTMCP_SHOW_SERVER_BANNER=false` and `FASTMCP_LOG_LEVEL=WARNING` unless `--verbose` is passed.

- **`probe/scorer.py`** does *structural* pass/fail only. It supports three expectation keys: `tools_called_includes`, `max_calls`, `answer_includes` (case-insensitive). If `answer` starts with `"ERROR:"` it returns FAIL early with the parsed error message — that prefix is the contract the runner uses to signal an API/transport failure.

- **`probe/judge.py`** does *semantic* pass/fail. It loads `probe/judge_prompt.txt` (an external template, not an inline string) and validates that the required placeholders `{task_prompt}`, `{tool_trace}`, `{answer}` and the required output fields `"verdict"`, `"reason"` are present before use. The judge model returns JSON; verdicts outside `{PASS, PARTIAL, FAIL, ERROR}` are coerced to `ERROR`. If you edit the prompt, keep those placeholders/fields and bump the `prompt_version:` comment — it gets parsed and stored in the judge file's `meta`.

- **`probe/config.py`** loads `probe.yaml` with shallow per-key overrides on top of hardcoded defaults — missing keys fall back, missing file falls back entirely. Always read config via `get_agent_model` / `get_judge_model` / `get_results_dir` / `get_judge_dir`, not by indexing the dict directly.

- **File naming is part of the contract.** Results files are `{server_stem}_{timestamp}_{model}_{run_id}.json`; judge files are `{results_stem}_judge_{judge_model}_{run_id}.json`. The `report` command finds a results file's judge by globbing `{results_stem}_judge_*.json` and picking the most recent by mtime — don't rename files by hand or this breaks. The model name in every filename always reflects the actual model used, never a placeholder.

## Things to keep consistent when changing code

- The runner's `"ERROR:"` answer prefix is load-bearing — scorer/reporter both special-case it. If you change the marker, update both.
- New expectation keys must be added in `probe/scorer.py` *and* documented in the `--help` output / README expectations list. The CLI's `--ignore-tool-names` flag pops `tools_called_includes` from each task's `expect` dict directly; any other future "ignore-X" flag should follow the same pattern.
- `eval --compare` and `full --compare` duplicate suite via `copy.deepcopy` before mutating it for the second server — preserve that, because the runner mutates the suite-derived task dicts and the two runs must stay independent.
- The judge prompt's required-placeholder check is enforced at load time, not at format time. If you add a new variable to the prompt, update both `REQUIRED_PLACEHOLDERS` and the `judge_task` call site.

## Reference servers and target API

`mcp_server_raw.py` and `mcp_server_semantic.py` both import the same six functions from `northwind_api.py` (which is plain SQLite, no MCP). The "raw" server is intentionally a naive 1:1 wrapper with terse docstrings; the "semantic" one adds rich descriptions, parameter notes, a `limit` cap on `orders()`, and a composite `order_with_details` tool. Treat `northwind_api.py` as the "untouchable legacy API" it's modeled on — the point of the demo is that you can only change the MCP layer, not the underlying data access.
