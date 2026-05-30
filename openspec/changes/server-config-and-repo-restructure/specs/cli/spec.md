## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: eval --ignore-tool-names removes tools_called_includes checks

**Reason**: The flag existed to strip `tools_called_includes` from task expectations when comparing servers with different tool names. With named server config, each task YAML controls its own expectations directly and no runtime stripping is needed.

**Migration**: Remove `--ignore-tool-names` from any `probe-mcp eval` or `probe-mcp full` invocations. If you need to run a task without tool-name checks, remove `tools_called_includes` from the task's `expect.deterministic` block in the YAML.
