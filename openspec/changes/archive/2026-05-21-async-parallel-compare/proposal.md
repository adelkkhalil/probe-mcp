## Why

When `--compare` is used, probe-mcp runs two full eval suites sequentially — the second server only starts after the first finishes. This doubles wall-clock time for every comparison run. Since the two suites share no state (they use separate MCP subprocesses, independent deep-copied task suites, and write to separate results files), they can safely run in parallel.

## What Changes

- The `eval` and `full` CLI commands run both server suites concurrently using `asyncio.gather` when `--compare` is provided.
- `run_suite` is invoked simultaneously for the primary and compare server; results are collected once both finish.
- Output order and file naming are unchanged — each server still gets its own results file with its own `run_id` and timestamp.
- Non-compare runs are unaffected.

## Capabilities

### New Capabilities

- `parallel-compare`: Concurrent execution of two `run_suite` calls via `asyncio.gather` when `--compare` is active, with result collection and display after both complete.

### Modified Capabilities

- `runner`: No requirement changes — `run_suite` signature and behavior are unchanged; parallelism lives entirely in the CLI call sites.
- `cli`: The `eval` and `full` commands acquire results from both servers before printing any output, replacing the sequential two-step pattern with a single `gather` call.

## Impact

- `probe/cli.py`: `eval` and `full` command handlers — replace sequential `_run_async(run_suite(...))` calls with a single `asyncio.gather` inside `_run_async`.
- No changes to `runner.py`, `scorer.py`, `reporter.py`, or `judge.py`.
- No new dependencies.
- No changes to results file format or naming convention.
