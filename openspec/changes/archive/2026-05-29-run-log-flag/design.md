## Context

`reporter.py` holds a module-level `console = Console()` that is also imported directly by `cli.py`. `judge.py` has its own `_console = Console()` for the per-task "Judged:" progress line. `runner.py` uses a bare `print()` for the "Running:" progress line. No module currently writes output anywhere other than the terminal — there is no log console object, no file writing, and no way to persist what the user sees.

## Goals / Non-Goals

**Goals:**
- Add `--log [DIR]` to `eval`, `judge`, `report`, and `full` commands
- When `--log` is active, write all terminal output to a plain-text file in parallel with the normal colored terminal output
- Plain-text log has no ANSI codes, no Rich markup, readable with any text editor
- All output goes through both consoles — no output should appear only in the terminal or only in the log

**Non-Goals:**
- Changing the terminal output in any way (no color removal, no format changes)
- Logging output from subprocesses or MCP server stderr
- Changing the JSON results or judge file format or naming
- Supporting multiple simultaneous log files per command
- Rotating or appending to existing log files

## Decisions

**Use Rich `Console(file=fp, no_color=True, markup=False, highlight=False)` for the log**

Rich's own `Console` can write to any file object. Setting `no_color=True` strips ANSI escape codes and `markup=False` prevents `[bold]` tags from appearing as literal text in the log. This is the idiomatic Rich approach — no custom stripping, no post-processing. The file stays open for the duration of the command and is flushed/closed when the `with` block exits.

**Thread `log_console` as an optional parameter (default `None`)**

Each function that produces output (`run_suite`, `judge_results_file`, `print_results`, `print_verdicts`, `print_compare_table`) receives an optional `log_console: Console | None = None` parameter. When `None`, behaviour is identical to today. This avoids mutating global state and makes the log console explicit. The CLI constructs the log console and passes it down; modules don't know or care whether a log is active.

**Change `runner.py` to use `console.print()` instead of bare `print()`**

The "Running: {task_id}" line in `run_suite` currently uses Python's built-in `print()`, which bypasses Rich entirely. To make it log-able, the runner must write through a Rich Console. `run_suite` will accept a `log_console` parameter and use the reporter module's `console` for the terminal side (already imported by CLI) for "Running:" lines.

**`--log` option implemented with Click's `flag_value` sentinel**

Click does not natively support options with optional values in a single declaration. The implementation uses `is_flag=False, flag_value=""` in Click: `--log` alone evaluates to `""` (use the results file's directory); `--log <dir>` evaluates to the provided path; omitted evaluates to `None` (no logging). The CLI resolves `""` to the results directory after the results file path is known.

**Log filename mirrors the results file with `.log` extension**

The log is named identically to the results file with `.json` replaced by `.log` (e.g. `results/server_2026-05-29_10-00_claude-haiku-4-5_3e1a.log`). For `report` (no new file created) and `judge` (no new results file), the log takes the base name of the input results file with `_report_<timestamp>.log` or `_judge_<timestamp>.log` suffix. The log file is opened before any output is produced and closed after all output completes.

**`report --log` falls back to results file stem + timestamp**

`report` reads an existing results file rather than creating one. When `--log` is active for `report`, the log filename is `{results_stem}_report_{timestamp}.log` in the log directory (which defaults to the same directory as the results file).

## Risks / Trade-offs

- **[Risk] `judge_results_file` is async and called via `_run_async`; log file must stay open across the async boundary** → The log file is opened in the CLI (synchronous context), the file handle is passed to `Console(file=fp)`, and the Console is passed into the async call. The file handle remains valid across the boundary; explicit `fp.close()` or `with` block in the CLI ensures cleanup.
- **[Risk] `--compare` runs two `run_suite` calls concurrently via `asyncio.gather`; both need the same log console** → Both suites share the same `log_console` instance. Rich's `Console` is not thread-safe for concurrent writes, but `asyncio.gather` runs in a single thread so interleaving is cooperative, not parallel — writes are safe.
- **[Risk] Adding `log_console` parameters to public-facing functions changes their signatures** → All new parameters have `default=None`, so existing callers (tests, scripts) are unaffected.
- **[Risk] Rich strips markup when writing to a file Console, but rule lines (`console.rule(...)`) may look odd as plain dashes** → Acceptable. Rich renders rules as lines of `─` characters in the file console just like any other text; the log remains readable.

## Migration Plan

No deployment steps. Rollback: revert changed files. No database, config, or external state involved. Log files are additive — existing results and judge files are unchanged.
