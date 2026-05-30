## MODIFIED Requirements

### Requirement: Results table displays task id, status, det score, pro score, and truncated answer

`print_results` SHALL render a Rich table with columns Task, Status, Det, Pro, and Answer. The Det column shows `N/M` (passed checks over total checks) from `det_score`. The Pro column shows `PASS (judge)`, `FAIL (judge)`, or `—` based on `pro_score` (`"pending"` renders as `—` since the judge has not run yet at score time; a resolved judge verdict passed in separately renders as the verdict). Answers longer than 80 characters are truncated with an ellipsis, preferring a word boundary when one exists past the 40-character mark.

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
- **THEN** the Pro cell shows `PASS (judge)` in bold green
