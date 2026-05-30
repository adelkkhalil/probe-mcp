# Spec: CLI

## Purpose

The CLI module is the entry point for probe-mcp. It uses Click to expose subcommands that wire together the loader, runner, scorer, judge, and reporter modules. It reads `PROBE_CWD` to resolve the user's original working directory when invoked via a uv alias.

## Requirements

### Requirement: Working directory is resolved via PROBE_CWD

The CLI SHALL use the `PROBE_CWD` environment variable as the working directory for locating task files, probe.yaml, and output directories. This preserves the user's original directory when uv changes cwd to the package directory.

#### Scenario: PROBE_CWD sets the effective working directory

- **WHEN** `PROBE_CWD=/home/user/myproject` is set in the environment
- **THEN** file operations in `init` and `status` resolve paths relative to `/home/user/myproject`

---

### Requirement: eval command runs tasks and saves results

The `eval` command SHALL accept a `tasks_file` argument, load the suite via the loader, run it via the runner, score each result, print the results table, and display the saved results file path.

#### Scenario: eval runs suite and prints saved path

- **WHEN** `probe-mcp eval tasks/my_server.yaml` is called
- **THEN** each task is run, results are scored and printed in a table
- **THEN** a line showing `Saved: <path>` is printed after the table

---

### Requirement: eval --server overrides the server from the task file

When `--server` is passed to `eval`, the CLI SHALL replace `suite["server"]` with the provided server name string before the loader resolves it against `servers.yaml`. The value is a server name, not a file path.

#### Scenario: --server replaces the suite server name

- **WHEN** `probe-mcp eval tasks/my_server.yaml --server raw` is called
- **THEN** the loader resolves `"raw"` from `servers.yaml` and the runner uses the resulting command/args

---

### Requirement: eval --compare runs two servers and prints a comparison table

When `--compare <server>` is passed, the CLI SHALL run the suite against both the primary server and the named compare server **concurrently** using independent deep copies of the suite, then print a side-by-side comparison table and individual result tables for both servers. No output is printed until both runs complete. The `--compare` value is a server name resolved via `servers.yaml`, not a file path.

#### Scenario: --compare produces comparison table and two result tables

- **WHEN** `probe-mcp eval tasks/my_server.yaml --compare raw` is called
- **THEN** both suites execute simultaneously via `asyncio.gather`
- **THEN** a comparison table with both server names as columns is printed after both complete
- **THEN** individual result tables for each server are printed and two `Saved:` lines are shown

#### Scenario: Output is withheld until both servers finish

- **WHEN** `--compare` is active and one server finishes before the other
- **THEN** no results or tables are printed until both `run_suite` calls have returned

---

### Requirement: eval --verbose passes through to runner and reporter

When `--verbose` is passed, the CLI SHALL propagate `verbose=True` to `run_suite` (disabling FastMCP log suppression) and to `print_results` (enabling full answer and check detail output).

#### Scenario: --verbose enables full output in runner and reporter

- **WHEN** `probe-mcp eval tasks/my_server.yaml --verbose` is called
- **THEN** `run_suite` is called with `verbose=True` and `print_results` is called with `verbose=True`

---

### Requirement: judge command runs semantic evaluation on a results file

The `judge` command SHALL accept a `results_file` argument, call `judge_results_file` with the configured or overridden judge model, print the verdicts table, and display the saved judge file path.

#### Scenario: judge saves and displays verdicts

- **WHEN** `probe-mcp judge results/server_2024-01-01_model_abcd.json` is called
- **THEN** verdicts are printed in a Rich table and a `Saved: <path>` line is printed

---

### Requirement: judge --model overrides the judge model from config

When `--model` is passed to `judge`, the CLI SHALL use that model string instead of the value from `probe.yaml`.

#### Scenario: --model overrides config model for judge command

- **WHEN** `probe-mcp judge results/file.json --model claude-opus-4-7` is called
- **THEN** `judge_results_file` is called with `judge_model="claude-opus-4-7"`

---

### Requirement: report command prints results and auto-discovers the judge file

The `report` command SHALL accept a `results_file` argument, print the scored results table, then search the judge directory for files matching `{results_stem}_judge_*.json`. If found, it prints the most recently modified matching file's verdicts. If not found, it prints a hint to run `probe-mcp judge`.

#### Scenario: report finds and prints matching judge file

- **WHEN** a judge file matching the results stem exists in the judge directory
- **THEN** `report` prints both the results table and the verdicts table

#### Scenario: report prints hint when no judge file exists

- **WHEN** no matching judge file exists in the judge directory
- **THEN** `report` prints the results table and a message suggesting `probe-mcp judge`

#### Scenario: report selects the most recent judge file when multiple exist

- **WHEN** multiple judge files match the results stem
- **THEN** `report` uses the one with the most recent modification time

---

### Requirement: full command runs eval then judge then report in sequence

The `full` command SHALL run `run_suite`, score results, print results, run `judge_results_file`, and print verdicts — all in one invocation. It accepts the same `--server`, `--compare`, `--judge-model`, and `--verbose` options as the individual commands. The `--ignore-tool-names` option is NOT accepted.

#### Scenario: full runs the complete pipeline and prints all output

- **WHEN** `probe-mcp full tasks/my_server.yaml` is called
- **THEN** the results table and the verdicts table are both printed
- **THEN** both the results file and the judge file `Saved:` paths are printed

#### Scenario: full --compare judges both servers

- **WHEN** `probe-mcp full tasks/my_server.yaml --compare raw` is called
- **THEN** both eval suites run concurrently, then the judge is run on each results file in turn
- **THEN** both verdict tables are printed and both `Saved:` paths for judge files are shown

---

### Requirement: init command creates probe.yaml, servers.yaml, and a sample tasks file

The `init` command SHALL create `probe.yaml`, `servers.yaml`, and `tasks/my_server.yaml` under the working directory if they do not exist, printing a confirmation for each file created. With `--force`, existing files are overwritten. The generated `servers.yaml` SHALL contain a commented example server entry. The generated `tasks/my_server.yaml` SHALL reference a server by name (e.g. `server: my_server`), not by file path.

#### Scenario: init creates missing files and prints confirmations

- **WHEN** none of `probe.yaml`, `servers.yaml`, or `tasks/my_server.yaml` exist
- **THEN** all three files are created and a confirmation is printed for each

#### Scenario: init skips existing files without --force

- **WHEN** `probe.yaml` already exists and `--force` is not passed
- **THEN** `probe.yaml` is not overwritten and a skip message is printed

#### Scenario: init --force overwrites existing files

- **WHEN** `probe.yaml` already exists and `--force` is passed
- **THEN** `probe.yaml` is overwritten and an overwrite confirmation is printed

#### Scenario: generated tasks file references server by name

- **WHEN** `probe-mcp init` creates `tasks/my_server.yaml`
- **THEN** the file contains `server: my_server` (a name, not a path)

---

### Requirement: status command displays config, servers, task files, results, and judge files

The `status` command SHALL render five sections: Config (current settings), Servers (all named servers from `servers.yaml` with their command and args), Task Files (all `.yaml` files under `tasks/` with task count and server), Results (all `.json` files in the results directory sorted by mtime descending with pass scores), and Judge Files (all `.json` files in the judge directory sorted by mtime descending with verdict counts). If `servers.yaml` is not found, the Servers section SHALL display a message indicating no servers are configured.

#### Scenario: status shows all five sections including servers

- **WHEN** `probe-mcp status` is called and `servers.yaml` exists with at least one entry
- **THEN** a Servers section lists each named server with its command and args alongside the Config, Task Files, Results, and Judge Files sections

#### Scenario: status shows no-servers message when servers.yaml is absent

- **WHEN** `servers.yaml` is not found in the task directory or PROBE_CWD
- **THEN** the Servers section prints a message suggesting to run `probe-mcp init` or create `servers.yaml`

#### Scenario: status shows no results message when directory is empty

- **WHEN** no results files exist in the results directory
- **THEN** the Results section prints a message suggesting to run `probe-mcp eval`

---

### Requirement: --log option enables plain-text output logging on eval, judge, report, and full

The `eval`, `judge`, `report`, and `full` commands SHALL each accept a `--log` option. When provided, the CLI SHALL open a plain-text log file, construct a Rich `Console(file=fp, highlight=False)`, and pass it as `log_console` to all downstream calls that produce output. The log file SHALL be closed after all output completes. Terminal output is unchanged.

#### Scenario: eval --log writes a log file alongside the results file

- **WHEN** `probe-mcp eval tasks/my_server.yaml --log` is called
- **THEN** a `.log` file is created in the same directory as the results file, containing all terminal output as plain text with no ANSI escape codes or Rich markup

#### Scenario: eval --log <dir> writes the log file to the specified directory

- **WHEN** `probe-mcp eval tasks/my_server.yaml --log logs/` is called
- **THEN** a `.log` file is created under `logs/` using the same base filename as the results file

#### Scenario: full --log writes a single log file covering eval, judge, and report output

- **WHEN** `probe-mcp full tasks/my_server.yaml --log` is called
- **THEN** a single `.log` file captures all Running:, Judged:, results table, and verdicts table output

#### Scenario: report --log writes a log file named after the results file stem

- **WHEN** `probe-mcp report results/server_2026-01-01_10-00_model_abcd.json --log` is called
- **THEN** a `.log` file is created in the same directory as the results file, named `server_2026-01-01_10-00_model_abcd_report_<timestamp>.log`

#### Scenario: judge --log writes a log file named after the results file stem

- **WHEN** `probe-mcp judge results/server_2026-01-01_10-00_model_abcd.json --log` is called
- **THEN** a `.log` file is created in the judge directory, named `server_2026-01-01_10-00_model_abcd_judge_<timestamp>.log`

#### Scenario: omitting --log produces no log file

- **WHEN** `probe-mcp eval tasks/my_server.yaml` is called without `--log`
- **THEN** no `.log` file is created and behaviour is identical to before

---

### Requirement: Log filename mirrors the results file with .log extension

When `--log` is active for `eval` or `full`, the log file SHALL be named identically to the results file but with `.log` replacing `.json`. The log file is placed in the directory specified by `--log`, or in the same directory as the results file when `--log` is used without a value.

#### Scenario: Log file shares the results file base name

- **WHEN** the results file is `results/server_2026-05-29_10-00_claude-haiku-4-5_3e1a.json` and `--log` is active
- **THEN** the log file is `results/server_2026-05-29_10-00_claude-haiku-4-5_3e1a.log` (default dir) or `<dir>/server_2026-05-29_10-00_claude-haiku-4-5_3e1a.log` (custom dir)

---

### Requirement: Terminal output is unchanged when --log is active

When `--log` is active, the CLI SHALL NOT alter the Rich-formatted terminal output in any way. Color, formatting, and table rendering in the terminal SHALL be identical whether or not `--log` is passed.

#### Scenario: --log does not affect terminal output appearance

- **WHEN** `probe-mcp eval tasks/my_server.yaml --log` is called
- **THEN** the terminal shows the same colored tables and styled text as without `--log`

---

### Requirement: CLI errors are reported as ClickExceptions

`FileNotFoundError` and `ValueError` raised by loader, runner, or judge SHALL be caught and re-raised as `click.ClickException`, causing Click to print a formatted error message and exit with status code 1.

#### Scenario: Missing task file prints click error and exits

- **WHEN** `probe-mcp eval nonexistent.yaml` is called
- **THEN** a formatted error message is printed and the process exits with code 1
