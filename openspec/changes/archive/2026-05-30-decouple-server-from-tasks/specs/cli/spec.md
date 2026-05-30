## MODIFIED Requirements

### Requirement: eval command runs tasks and saves results

The `eval` command SHALL accept a `tasks_file` argument and a required `--server <name>` option. It SHALL load the suite via the loader (passing `server_name`), run it via the runner, score each result, print the results table, and display the saved results file path. When `--server` is omitted, Click SHALL display a `Missing option '--server'` error and exit with code 1.

#### Scenario: eval runs suite and prints saved path

- **WHEN** `probe-mcp eval tasks/my_server.yaml --server semantic` is called
- **THEN** each task is run, results are scored and printed in a table
- **THEN** a line showing `Saved: <path>` is printed after the table

#### Scenario: eval without --server exits with error

- **WHEN** `probe-mcp eval tasks/my_server.yaml` is called without `--server`
- **THEN** Click prints `Error: Missing option '--server'.` and exits with code 1

---

### Requirement: eval --server specifies the required server name

`--server` on `eval` is a required option with no default. The CLI SHALL pass the value as `server_name` to `load_tasks()`. The value is a server name resolved against `servers.yaml`, not a file path. When the name is not found in `servers.yaml`, the error message SHALL list the available server names.

#### Scenario: --server provides the server name to load_tasks

- **WHEN** `probe-mcp eval tasks/my_server.yaml --server raw` is called
- **THEN** `load_tasks(tasks_file, server_name="raw")` is called and the loader resolves `"raw"` from `servers.yaml`

#### Scenario: --server with unknown name shows available servers

- **WHEN** `probe-mcp eval tasks/my_server.yaml --server nonexistent` is called and `servers.yaml` has `semantic` and `raw`
- **THEN** a `ClickException` is raised with a message naming `nonexistent` and listing `semantic, raw`

---

### Requirement: eval --compare runs two servers and prints a comparison table

When `--compare <server>` is passed, the CLI SHALL run the suite against both the primary server (from `--server`) and the named compare server **concurrently** using independent calls to `load_tasks()` with each server name, then print a side-by-side comparison table and individual result tables for both servers. No output is printed until both runs complete. The `--compare` value is a server name resolved via `servers.yaml`, not a file path.

#### Scenario: --compare produces comparison table and two result tables

- **WHEN** `probe-mcp eval tasks/my_server.yaml --server semantic --compare raw` is called
- **THEN** both suites execute simultaneously via `asyncio.gather`
- **THEN** a comparison table with both server names as columns is printed after both complete
- **THEN** individual result tables for each server are printed and two `Saved:` lines are shown

#### Scenario: Output is withheld until both servers finish

- **WHEN** `--compare` is active and one server finishes before the other
- **THEN** no results or tables are printed until both `run_suite` calls have returned

---

### Requirement: full command runs eval then judge then report in sequence

The `full` command SHALL accept a `tasks_file` argument and a required `--server <name>` option. It SHALL run `run_suite`, score results, print results, run `judge_results_file`, and print verdicts — all in one invocation. It accepts the same `--server`, `--compare`, `--judge-model`, and `--verbose` options as the individual commands. When `--server` is omitted, Click SHALL display a `Missing option '--server'` error and exit with code 1. The `--ignore-tool-names` option is NOT accepted.

#### Scenario: full runs the complete pipeline and prints all output

- **WHEN** `probe-mcp full tasks/my_server.yaml --server semantic` is called
- **THEN** the results table and the verdicts table are both printed
- **THEN** both the results file and the judge file `Saved:` paths are printed

#### Scenario: full without --server exits with error

- **WHEN** `probe-mcp full tasks/my_server.yaml` is called without `--server`
- **THEN** Click prints `Error: Missing option '--server'.` and exits with code 1

#### Scenario: full --compare judges both servers

- **WHEN** `probe-mcp full tasks/my_server.yaml --server semantic --compare raw` is called
- **THEN** both eval suites run concurrently, then the judge is run on each results file in turn
- **THEN** both verdict tables are printed and both `Saved:` paths for judge files are shown

---

### Requirement: init command creates probe.yaml, servers.yaml, and a sample tasks file

The `init` command SHALL create `probe.yaml`, `servers.yaml`, and `tasks/my_server.yaml` under the working directory if they do not exist, printing a confirmation for each file created. With `--force`, existing files are overwritten. The generated `servers.yaml` SHALL contain a commented example server entry. The generated `tasks/my_server.yaml` SHALL contain only `tasks` — no `server:` field.

#### Scenario: init creates missing files and prints confirmations

- **WHEN** none of `probe.yaml`, `servers.yaml`, or `tasks/my_server.yaml` exist
- **THEN** all three files are created and a confirmation is printed for each

#### Scenario: init skips existing files without --force

- **WHEN** `probe.yaml` already exists and `--force` is not passed
- **THEN** `probe.yaml` is not overwritten and a skip message is printed

#### Scenario: init --force overwrites existing files

- **WHEN** `probe.yaml` already exists and `--force` is passed
- **THEN** `probe.yaml` is overwritten and an overwrite confirmation is printed

#### Scenario: generated tasks file contains no server field

- **WHEN** `probe-mcp init` creates `tasks/my_server.yaml`
- **THEN** the file does NOT contain a `server:` field; it contains only `tasks`
