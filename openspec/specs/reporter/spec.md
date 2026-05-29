# Spec: Reporter

## Purpose

The reporter renders evaluation results and judge verdicts to the terminal using Rich tables and styled text. It is a pure display module — it does not perform file I/O, scoring, or API calls.

## Requirements

### Requirement: Results table displays task id, status, det score, pro score, call count, and truncated answer

`print_results` SHALL render a Rich table with columns Task, Status, Det, Pro, Calls, and Answer. The Det column shows `N/M` (passed checks over total checks) from `det_score`. The Pro column shows a styled judge verdict, or `—` when no probabilistic section was declared or the judge has not yet run. Answers longer than 80 characters are truncated with an ellipsis, preferring a word boundary when one exists past the 40-character mark.

#### Scenario: Long answer is truncated at word boundary

- **WHEN** a task answer is longer than 80 characters and contains spaces
- **THEN** the Answer cell shows at most 80 characters followed by `"..."`

#### Scenario: Short answer is shown in full

- **WHEN** a task answer is 30 characters or fewer
- **THEN** the Answer cell shows the full text without truncation

#### Scenario: Det column shows pass ratio

- **WHEN** a scored result has `det_score: {"passed": 2, "total": 3}`
- **THEN** the Det cell shows `2/3`

#### Scenario: Pro column shows dash when no probabilistic section

- **WHEN** a scored result has `pro_score: null`
- **THEN** the Pro cell shows `—`

#### Scenario: Pro column shows judge verdict when resolved

- **WHEN** the judge has run and the task's verdict is `"PASS"`
- **THEN** the Pro cell shows `✓ PASS (judge)` in bold green

---

### Requirement: Status cells use color-coded styled text

`print_results` SHALL render the status cell using Rich styled Text: PASS as bold green with `✓ PASS`, FAIL as bold red with `✗ FAIL`, PARTIAL as bold blue with `~ PARTIAL`, WARN as bold yellow with `! WARN`, and ERROR as bold yellow with `! ERROR`.

#### Scenario: PASS status renders as bold green

- **WHEN** a scored result has `"status": "PASS"`
- **THEN** the Status cell shows `✓ PASS` in bold green

#### Scenario: FAIL status renders as bold red

- **WHEN** a scored result has `"status": "FAIL"`
- **THEN** the Status cell shows `✗ FAIL` in bold red

---

### Requirement: Error answers are displayed in red with message extraction

When an answer starts with `"ERROR:"`, the reporter SHALL attempt to extract a human-readable message by searching for `'message': '<text>'` in the string. If found, the extracted text is shown; otherwise the raw answer after `"ERROR:"` is used. The result is rendered in bold red.

#### Scenario: Structured error message is extracted

- **WHEN** answer is `"ERROR: {'message': 'connection refused'}"`
- **THEN** the Answer cell shows `"connection refused"` in bold red

#### Scenario: Unstructured error falls back to raw slice

- **WHEN** answer is `"ERROR: something went wrong"` with no `message` key
- **THEN** the Answer cell shows `"something went wrong"` in bold red

---

### Requirement: Verbose mode shows full answers and check detail lines

When `verbose=True` is passed to `print_results`, the reporter SHALL print each individual passed and failed check line after the table, followed by the full untruncated answer for every task.

#### Scenario: Verbose mode prints full answers

- **WHEN** `print_results(scored, server_name, verbose=True)` is called
- **THEN** full answers for each task are printed below the table

#### Scenario: Verbose mode prints failed check lines in red

- **WHEN** a task has failed checks and `verbose=True`
- **THEN** each failed message is printed in bold red below the table

---

### Requirement: Summary line shows pass count over total

`print_results` SHALL print a bold summary line of the form `Results: N/M passed` before the table.

#### Scenario: Summary reflects correct pass and total counts

- **WHEN** 3 of 5 tasks have `"status": "PASS"`
- **THEN** the output contains `"Results: 3/5 passed"`

---

### Requirement: Verdicts table displays task id, verdict, and reason

`print_verdicts` SHALL render a Rich table with columns Task, Verdict, and Reason. Verdicts are styled: PASS as bold green with `✓ PASS`, PARTIAL as bold blue with `~ PARTIAL`, FAIL as bold red with `✗ FAIL`, ERROR as bold yellow with `! ERROR`.

#### Scenario: PARTIAL verdict renders as bold blue

- **WHEN** a verdict entry has `"verdict": "PARTIAL"`
- **THEN** the Verdict cell shows `~ PARTIAL` in bold blue

#### Scenario: ERROR verdict renders as bold yellow

- **WHEN** a verdict entry has `"verdict": "ERROR"`
- **THEN** the Verdict cell shows `! ERROR` in bold yellow

---

### Requirement: Results table shows consistency score when any task used trials

When any scored result in the list contains a `consistency_score` field, `print_results` SHALL add a `Consistency` column to the results table. For tasks with `consistency_score`, the cell shows the score as a percentage (e.g., `100%`, `67%`). For tasks without a `consistency_score`, the cell shows `—`.

#### Scenario: Consistency column appears when at least one task has trials

- **WHEN** at least one scored result has a `consistency_score` field
- **THEN** the results table includes a `Consistency` column

#### Scenario: Perfect consistency renders as 100%

- **WHEN** a scored result has `consistency_score: 1.0`
- **THEN** the Consistency cell shows `100%` in bold green

#### Scenario: Partial consistency renders in yellow

- **WHEN** a scored result has `consistency_score: 0.67`
- **THEN** the Consistency cell shows `67%` in bold yellow

#### Scenario: Zero consistency renders in red

- **WHEN** a scored result has `consistency_score: 0.0`
- **THEN** the Consistency cell shows `0%` in bold red

#### Scenario: Task without trials shows dash in consistency column

- **WHEN** a scored result has no `consistency_score` field and the table includes a Consistency column
- **THEN** the Consistency cell for that task shows `—`

---

### Requirement: Compare table shows both servers side by side

`print_compare_table` SHALL render a Rich table with columns Task, server1_name, and server2_name. Each status cell shows the status label with the call count in parentheses.

#### Scenario: Compare table includes call counts in status cells

- **WHEN** a task for server1 has status PASS and call_count 3
- **THEN** the server1 column cell shows `✓ PASS (3)`

#### Scenario: Missing task in server2 renders as FAIL

- **WHEN** server2 has no result for a given task id
- **THEN** the server2 column cell for that task shows `FAIL` in red
