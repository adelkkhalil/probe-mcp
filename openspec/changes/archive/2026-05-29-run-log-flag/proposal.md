## Why

Terminal output from `probe-mcp` — scoring tables, verdict summaries, running status lines — disappears after the session. There is no way to capture it alongside the structured JSON results, making it hard to share run summaries or audit what happened without re-running.

## What Changes

- **`--log` flag on `eval`, `judge`, `report`, and `full` commands** — when provided, all terminal output for that command is written to a plain-text file (Rich markup and ANSI escape codes stripped)
- **`--log <dir>`** — writes the log to the specified directory using the same base filename as the results file but with `.log` extension
- **`--log` without a value** — defaults to the same directory as the results file (or `results/` for `report` / `judge`)
- **Log filename mirrors results filename**: `results/mcp_server_semantic_2026-05-29_19-40_claude-haiku-4-5_3e1a.log`
- **Terminal output is unchanged** — Rich color output continues to render normally; the log is a parallel write, not a redirect
- Plain-text log uses Rich's `Console(file=..., no_color=True, markup=False)` — no ANSI codes, no markup characters

## Capabilities

### New Capabilities

_(none — all changes extend existing capabilities)_

### Modified Capabilities

- `cli`: new `--log` option (optional path) added to `eval`, `judge`, `report`, and `full` commands; log console constructed and threaded through to downstream calls
- `reporter`: `print_results`, `print_verdicts`, and `print_compare_table` accept an optional `log_console` parameter and mirror all output to it when provided
- `judge`: `judge_results_file` and its per-task progress output accept an optional `log_console` parameter and mirror judging lines to it when provided
- `runner`: `run_suite` accepts an optional `log_console` parameter and mirrors `Running: <task_id>` lines to it when provided

## Impact

- `probe/cli.py` — `--log` option on four commands; log `Console` construction; pass `log_console` down to runner, reporter, judge
- `probe/reporter.py` — optional `log_console` parameter on `print_results`, `print_verdicts`, `print_compare_table`
- `probe/judge.py` — optional `log_console` parameter on `judge_results_file` (per-task progress lines)
- `probe/runner.py` — optional `log_console` parameter on `run_suite` (`Running:` lines)
- No changes to JSON result format, file naming convention, or existing CLI options
