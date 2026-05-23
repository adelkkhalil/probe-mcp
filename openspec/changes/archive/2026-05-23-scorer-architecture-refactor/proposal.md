## Why

The flat `expect:` dict conflates two fundamentally different kinds of evaluation — mechanical checks that run from the tool trace (deterministic) and judgment calls that require an LLM (probabilistic) — with no structural signal distinguishing them. Making that split explicit in the YAML schema gives task authors a clear mental model, makes the scorer's scope unambiguous, and creates a natural extension point for future probabilistic check types beyond `judge: true`.

## What Changes

- **BREAKING**: `expect:` keys (`tools_called_includes`, `max_calls`, `answer_includes`) must move under `expect.deterministic:` in all task YAML files
- New optional `expect.probabilistic:` sub-dict accepts `judge: true` to opt a task into LLM judging
- `probe/scorer.py` reads expectations from `expect["deterministic"]` instead of `expect` directly
- `probe/loader.py` validates the new nested structure; emits a deprecation warning (not error) when flat expectation keys are found at the top-level `expect:` dict for backward compatibility
- `probe/reporter.py` results table gains a `Det` column (`det: N/M passed`) and a `Pro` column (`pro: PASS (judge)` or `pro: —` when absent); overall `Status` column remains
- `tasks/northwind.yaml` migrated to new format
- Results JSON gains two new optional fields `det_score` (`{passed: N, total: M}`) and `pro_score` (`"PASS"` / `"FAIL"` / `null`) for downstream tooling; existing fields unchanged
- `openspec/specs/scorer/spec.md`, `openspec/specs/loader/spec.md`, `openspec/specs/reporter/spec.md` updated to reflect new requirements
- `README.md` writing-tasks section updated with new YAML format

What does **not** change:
- Scoring logic inside each individual check
- The judge pipeline (`probe/judge.py`)
- CLI commands and flags
- Core results JSON fields (backward compatible additions only)

## Capabilities

### New Capabilities

_(none — this is an architecture refactor of existing capabilities)_

### Modified Capabilities

- `scorer`: requirements change from reading `expect` flat dict to reading `expect["deterministic"]` sub-dict
- `loader`: validation requirements change to enforce new nested structure and emit deprecation warning on legacy flat keys
- `reporter`: output format requirements change to display deterministic and probabilistic scores as separate columns in the results table

## Impact

- `probe/scorer.py` — key reads pivot to `expect.get("deterministic", {})`
- `probe/loader.py` — validation logic added for nested structure; backward compat warning path added
- `probe/reporter.py` — results table columns updated; `det_score` / `pro_score` fields read from scored results
- `tasks/northwind.yaml` — all four tasks migrated to nested format
- `openspec/specs/scorer/spec.md`, `openspec/specs/loader/spec.md`, `openspec/specs/reporter/spec.md` — delta specs applied
- `README.md` — task authoring section
- No changes to `probe/runner.py`, `probe/judge.py`, `probe/config.py`, `probe/cli.py`
