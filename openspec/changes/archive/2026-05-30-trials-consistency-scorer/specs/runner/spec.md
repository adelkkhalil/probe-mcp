## ADDED Requirements

### Requirement: trials support runs a task N times when trials > 1
When a task's `expect["deterministic"]` contains `trials` with a value greater than 1, the runner SHALL execute `run_task` exactly N times for that task. Each execution produces an independent `{trace, answer}` result. The aggregated result stored in the results list SHALL contain:

- `"trace"` and `"answer"` from the first trial (for backwards compatibility with the scorer and reporter)
- `"trials"`: a list of N `{trace, answer}` dicts, one per execution

When `trials` is 1 or absent, the runner's output is unchanged (no `"trials"` key added).

#### Scenario: Task with trials: 3 produces three raw results
- **WHEN** `expect["deterministic"]["trials"]` is `3` for a task
- **THEN** the result dict for that task contains a `"trials"` list with exactly 3 entries, each having `"trace"` and `"answer"` keys

#### Scenario: Task without trials produces unchanged result
- **WHEN** `expect["deterministic"]` has no `"trials"` key
- **THEN** the result dict has no `"trials"` key and is structured exactly as before
