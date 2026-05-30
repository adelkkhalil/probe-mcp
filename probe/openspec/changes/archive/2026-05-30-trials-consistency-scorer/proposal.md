## Why

The runner currently executes each task once, so there is no way to distinguish a tool description that is reliably clear from one that produces inconsistent agent behaviour across repeated calls. Adding a `trials` field lets users measure consistency — a score of 1.0 means the tool description is unambiguous; anything below 0.7 is a signal that the description needs work.

## What Changes

- `probe/loader.py` — validate a new optional `trials: int` field on each task (must be ≥ 1, default 1)
- `probe/runner.py` — when `trials > 1`, execute the task N times and collect all answers and tool traces
- `probe/scorer.py` — compute a consistency score across trial runs (fraction of runs matching the most common answer)
- `probe/reporter.py` — show a Consistency column when any task has `trials > 1`; hide it otherwise
- `tasks/northwind.yaml` — add `trials: 3` to at least one task as a working example
- Spec files for runner, scorer, and reporter updated to reflect the new behaviour

## Capabilities

### New Capabilities
- `trials-consistency`: Per-task `trials` field that drives N repeated runs and a consistency score measuring agreement across answers

### Modified Capabilities
- `runner`: Requirements change — must support running a task N times and returning all trial answers/traces
- `scorer`: Requirements change — must compute a consistency score alongside existing deterministic checks
- `reporter`: Requirements change — must conditionally display a Consistency column when trials > 1

## Impact

- **probe/loader.py** — new field validation
- **probe/runner.py** — loop over N trials, aggregate results
- **probe/scorer.py** — consistency score computation (most-common-answer fraction)
- **probe/reporter.py** — conditional Consistency column in Rich table
- **tasks/northwind.yaml** — example task with `trials: 3`
- Results JSON schema gains a `trials` array per task result
- No changes to `probe/config.py`, `probe/judge.py`, or the judge prompt
