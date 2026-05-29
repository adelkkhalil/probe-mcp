## Why

The current scorer covers only the three most basic structural signals — which tools were called, how many times, and what the answer contains. Real-world eval suites need finer-grained assertions: what tools were deliberately avoided, what parameters were passed, what must be absent from the answer, whether calls happened in the right sequence, and whether the agent arrives at the same answer consistently across runs. Adding these checks keeps evaluation fully deterministic (no LLM cost, instant feedback) while dramatically increasing the signal available per task.

## What Changes

**Phase 1 — six new deterministic checks under `expect.deterministic`:**

- `tools_called_excludes: [list]` — fails if any listed tool appears in the trace
- `tool_called_count: int` — fails if trace length ≠ exact expected count
- `tool_params_include: {tool: name, params: [key1, key2]}` — fails if the named tool was not called with all listed parameter keys present
- `answer_excludes: string` — fails if the string appears anywhere in the answer (case-insensitive)
- `no_error: true` — fails if any tool call in the trace returned an error result
- `tools_called_sequence: [tool1, tool2, ...]` — fails if the tools do not appear in this relative order in the trace (subset match, not exhaustive)
- `probe/scorer.py` updated with all six checks
- `probe/loader.py` updated with validation for all six keys
- `tasks/northwind.yaml` updated with examples; new UAE banking/e-commerce task YAML examples added

**Phase 2 — trials consistency scoring under `expect.deterministic`:**

- `trials: int` (default 1) — runs the task N times and reports a consistency score across runs
- `probe/runner.py` updated to run a task N times when `trials > 1`, returning all N results
- `probe/reporter.py` updated to display a consistency score column when any task has `trials > 1`
- `probe/scorer.py` updated to aggregate multi-trial results into a consistency score
- `probe/loader.py` updated to validate `trials` as a positive integer

## Capabilities

### New Capabilities

_(none — all changes extend existing capabilities)_

### Modified Capabilities

- `scorer`: six new deterministic check requirements (Phase 1); trials consistency aggregation requirement (Phase 2)
- `loader`: validation requirements for six new keys (Phase 1); `trials` key validation (Phase 2)
- `runner`: trials execution requirement — run task N times when `trials > 1` (Phase 2)
- `reporter`: consistency score display requirement when trials > 1 (Phase 2)

## Impact

- `probe/scorer.py` — six new `if key in det:` blocks (Phase 1); consistency aggregation logic (Phase 2)
- `probe/loader.py` — type/shape validation for six new keys (Phase 1); `trials` int validation (Phase 2)
- `probe/runner.py` — loop task execution N times when trials > 1 (Phase 2)
- `probe/reporter.py` — consistency column in results table (Phase 2)
- `tasks/northwind.yaml` — new check examples on existing tasks
- No changes to `probe/judge.py`, `probe/config.py`, `probe/cli.py`, or result file naming
