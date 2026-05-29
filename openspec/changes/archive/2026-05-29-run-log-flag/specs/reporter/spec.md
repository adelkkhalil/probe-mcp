## ADDED Requirements

### Requirement: print_results mirrors output to log_console when provided

When `print_results` is called with a non-None `log_console` parameter, it SHALL write all output — the rule line, the summary line, the Rich table, and any verbose detail lines — to `log_console` in addition to the main terminal console. When `log_console` is `None`, behaviour is identical to before.

#### Scenario: print_results writes to both consoles when log_console is provided

- **WHEN** `print_results(scored, server_name, log_console=lc)` is called with a valid `log_console`
- **THEN** the results rule, summary line, and table are written to both the terminal console and `lc`

#### Scenario: print_results is unchanged when log_console is None

- **WHEN** `print_results(scored, server_name)` is called without `log_console`
- **THEN** output goes only to the terminal console, identical to previous behaviour

---

### Requirement: print_verdicts mirrors output to log_console when provided

When `print_verdicts` is called with a non-None `log_console` parameter, it SHALL write the verdicts rule line and the verdicts table to `log_console` in addition to the main terminal console.

#### Scenario: print_verdicts writes to both consoles when log_console is provided

- **WHEN** `print_verdicts(verdicts, judge_model, log_console=lc)` is called with a valid `log_console`
- **THEN** the verdicts rule and table are written to both the terminal console and `lc`

---

### Requirement: print_compare_table mirrors output to log_console when provided

When `print_compare_table` is called with a non-None `log_console` parameter, it SHALL write the comparison rule line and the comparison table to `log_console` in addition to the main terminal console.

#### Scenario: print_compare_table writes to both consoles when log_console is provided

- **WHEN** `print_compare_table(scored1, scored2, s1, s2, log_console=lc)` is called with a valid `log_console`
- **THEN** the comparison rule and table are written to both the terminal console and `lc`
