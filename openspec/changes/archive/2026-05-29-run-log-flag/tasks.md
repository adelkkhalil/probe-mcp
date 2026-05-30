## 1. Reporter — log_console Parameter

- [x] 1.1 In `probe/reporter.py`, add `log_console: Console | None = None` parameter to `print_results`; after each `console.print(...)` or `console.rule(...)` call, add a mirrored `if log_console: log_console.print(...)` / `log_console.rule(...)` call
- [x] 1.2 In `probe/reporter.py`, add `log_console: Console | None = None` parameter to `print_verdicts`; mirror all console output to `log_console` when provided
- [x] 1.3 In `probe/reporter.py`, add `log_console: Console | None = None` parameter to `print_compare_table`; mirror all console output to `log_console` when provided

## 2. Runner — log_console Parameter

- [x] 2.1 In `probe/runner.py`, import `Console` from `rich.console`; replace the bare `print(f"Running: {task['id']}")` call in `run_suite` with `console.print(f"Running: {task['id']}")` using the reporter module's console (import it from `probe.reporter`)
- [x] 2.2 In `probe/runner.py`, add `log_console: Console | None = None` parameter to `run_suite`; mirror each `Running:` line to `log_console` when provided

## 3. Judge — log_console Parameter

- [x] 3.1 In `probe/judge.py`, add `log_console: Console | None = None` parameter to `judge_results_file`; mirror each `_console.print(f"[dim]Judged: ...")` line to `log_console` when provided

## 4. CLI — --log Option and Console Construction

- [x] 4.1 In `probe/cli.py`, add `@click.option("--log", "log_dir", default=None, is_flag=False, flag_value="", metavar="[DIR]", help="Write plain-text log to DIR (default: alongside results)")` to the `eval` command
- [x] 4.2 In `probe/cli.py`, add the same `--log` option to the `judge` command
- [x] 4.3 In `probe/cli.py`, add the same `--log` option to the `report` command
- [x] 4.4 In `probe/cli.py`, add the same `--log` option to the `full` command
- [x] 4.5 In `probe/cli.py`, add a helper `_make_log_console(log_dir: str | None, results_path: str, suffix: str = "") -> tuple[Console | None, IO | None]` that: returns `(None, None)` when `log_dir is None`; resolves `log_dir=""` to the directory of `results_path`; constructs the log filename as `Path(results_path).stem + suffix + ".log"`; opens the file, constructs `Console(file=fp, no_color=True, markup=False, highlight=False)`; returns `(console, fp)`
- [x] 4.6 In the `eval` command, after `results_file` is known, call `_make_log_console(log_dir, results_file)`, pass `log_console` to `print_results` and `console.print(f"[dim]Saved: ...")` mirror; close the file handle after all output
- [x] 4.7 In the `judge` command, call `_make_log_console(log_dir, results_file, suffix="_judge_<timestamp>")` before running, pass `log_console` to `judge_results_file` and `print_verdicts`; close handle after
- [x] 4.8 In the `report` command, call `_make_log_console(log_dir, results_file, suffix="_report_<timestamp>")`, pass `log_console` to `print_results` and `print_verdicts`; close handle after
- [x] 4.9 In the `full` command, construct the log console after `results_file` is known and pass it to `run_suite`, `print_results`, `judge_results_file`, and `print_verdicts` (and their compare variants); close handle after all output

## 5. Specs — Delta Applied

- [x] 5.1 Apply delta spec: merge `openspec/changes/run-log-flag/specs/cli/spec.md` ADDED requirements into `openspec/specs/cli/spec.md`
- [x] 5.2 Apply delta spec: merge `openspec/changes/run-log-flag/specs/reporter/spec.md` ADDED requirements into `openspec/specs/reporter/spec.md`
- [x] 5.3 Apply delta spec: merge `openspec/changes/run-log-flag/specs/judge/spec.md` ADDED requirements into `openspec/specs/judge/spec.md`
- [x] 5.4 Apply delta spec: merge `openspec/changes/run-log-flag/specs/runner/spec.md` MODIFIED + ADDED requirements into `openspec/specs/runner/spec.md`
