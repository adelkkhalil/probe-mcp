# Spec: Reporter

## Purpose

The reporter renders evaluation results and judge verdicts to the terminal using Rich tables and styled text. It is a pure display module — it does not perform file I/O, scoring, or API calls.

## Requirements

### Requirement: Results table displays task id, status, call count, and truncated answer

`print_results` SHALL render a Rich table with columns Task, Status, Calls, and Answer. Answers longer than 80 characters are truncated with an ellipsis, preferring a word boundary when one exists past the 40-character mark.

#### Scenario: Long answer is truncated at word boundary

- **WHEN** a task answer is longer than 80 characters and contains spaces
- **THEN** the Answer cell shows at most 80 characters followed by `"..."`

#### Scenario: Short answer is shown in full

- **WHEN** a task answer is 30 characters or fewer
- **THEN** the Answer cell shows the full text without truncation

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

### Requirement: Compare table shows both servers side by side

`print_compare_table` SHALL render a Rich table with columns Task, server1_name, and server2_name. Each status cell shows the status label with the call count in parentheses.

#### Scenario: Compare table includes call counts in status cells

- **WHEN** a task for server1 has status PASS and call_count 3
- **THEN** the server1 column cell shows `✓ PASS (3)`

#### Scenario: Missing task in server2 renders as FAIL

- **WHEN** server2 has no result for a given task id
- **THEN** the server2 column cell for that task shows `FAIL` in red
