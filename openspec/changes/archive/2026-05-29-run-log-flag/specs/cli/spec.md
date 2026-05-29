## ADDED Requirements

### Requirement: --log option enables plain-text output logging on eval, judge, report, and full

The `eval`, `judge`, `report`, and `full` commands SHALL each accept a `--log` option. When provided, the CLI SHALL open a plain-text log file, construct a Rich `Console(file=fp, no_color=True, markup=False, highlight=False)`, and pass it as `log_console` to all downstream calls that produce output. The log file SHALL be closed after all output completes.

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
