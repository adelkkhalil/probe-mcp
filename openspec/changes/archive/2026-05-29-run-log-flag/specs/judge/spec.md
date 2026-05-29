## ADDED Requirements

### Requirement: judge_results_file mirrors per-task progress to log_console when provided

When `judge_results_file` is called with a non-None `log_console` parameter, it SHALL write each per-task "Judged: {id} → {verdict}" progress line to `log_console` in addition to the module's internal console. When `log_console` is `None`, behaviour is identical to before.

#### Scenario: Judged progress lines appear in log file when log_console is provided

- **WHEN** `judge_results_file(results_path, model, judge_dir, log_console=lc)` is called
- **THEN** each `Judged: <task_id> → <verdict>` line is written to both the terminal console and `lc`

#### Scenario: judge_results_file is unchanged when log_console is None

- **WHEN** `judge_results_file(results_path, model, judge_dir)` is called without `log_console`
- **THEN** output goes only to the module's internal console, identical to previous behaviour
