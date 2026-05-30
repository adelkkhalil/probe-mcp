## 1. Runner — Trace Error Flag

- [x] 1.1 In `probe/runner.py`, update `run_task` to capture `result.isError` from `session.call_tool` and include it as `"error": bool` in each trace entry: `{"tool": ..., "params": ..., "error": result.isError}`

## 2. Loader — Validate New Phase 1 Keys

- [x] 2.1 In `probe/loader.py`, add validation for `tools_called_excludes`: must be a list of strings when present under `expect.deterministic`
- [x] 2.2 In `probe/loader.py`, add validation for `tool_called_count`: must be a non-negative integer (reject booleans) when present under `expect.deterministic`
- [x] 2.3 In `probe/loader.py`, add validation for `tool_params_include`: must be a dict with a non-empty string `tool` key and a `params` key that is a list of strings
- [x] 2.4 In `probe/loader.py`, add validation for `answer_excludes`: must be a string when present under `expect.deterministic`
- [x] 2.5 In `probe/loader.py`, add validation for `no_error`: must be the boolean `True` (reject `False` and non-booleans) when present under `expect.deterministic`
- [x] 2.6 In `probe/loader.py`, add validation for `tools_called_sequence`: must be a list of strings when present under `expect.deterministic`

## 3. Scorer — Six New Phase 1 Checks

- [x] 3.1 In `probe/scorer.py`, add `tools_called_excludes` check: for each tool in the list, fail if it appears in `tools_called`, pass if absent
- [x] 3.2 In `probe/scorer.py`, add `tool_called_count` check: pass if `len(trace) == det["tool_called_count"]`, fail otherwise
- [x] 3.3 In `probe/scorer.py`, add `tool_params_include` check: find all calls to `det["tool_params_include"]["tool"]` in the trace; pass if any call's `params` dict contains all keys in `det["tool_params_include"]["params"]`; fail if no matching call or tool never called
- [x] 3.4 In `probe/scorer.py`, add `answer_excludes` check: fail if `det["answer_excludes"].lower()` is found in `answer.lower()`, pass otherwise
- [x] 3.5 In `probe/scorer.py`, add `no_error` check: count trace entries where `entry.get("error", False) is True`; pass if count is 0, fail with count otherwise
- [x] 3.6 In `probe/scorer.py`, add `tools_called_sequence` check: walk the trace to verify the listed tools appear as a subsequence in order; pass if the full sequence is satisfied, fail otherwise

## 4. Task YAML Examples

- [x] 4.1 In `tasks/northwind.yaml`, add `tools_called_sequence` to `orders_by_shipper` task (shippers before orders), `no_error: true` to at least one task, and `tool_called_count` to `customers_by_country`
- [x] 4.2 Create `tasks/uae_banking.yaml` with 3 tasks demonstrating: `tools_called_excludes` (no history call for balance check), `tool_params_include` (iban param present), and `answer_excludes` (IBAN not exposed in answer)

## 5. Specs — Phase 1 Delta Applied

- [x] 5.1 Apply delta spec: merge `openspec/changes/deterministic-scorers-expansion/specs/scorer/spec.md` ADDED requirements (Phase 1 checks only — skip `consistency_score`) into `openspec/specs/scorer/spec.md`
- [x] 5.2 Apply delta spec: merge `openspec/changes/deterministic-scorers-expansion/specs/loader/spec.md` ADDED requirements (Phase 1 keys only — skip `trials`) into `openspec/specs/loader/spec.md`
- [x] 5.3 Apply delta spec: merge `openspec/changes/deterministic-scorers-expansion/specs/runner/spec.md` MODIFIED requirement (trace error flag) into `openspec/specs/runner/spec.md`

## 6. Loader — Validate trials (Phase 2)

- [x] 6.1 In `probe/loader.py`, add validation for `trials` under `expect.deterministic`: must be a positive integer > 0 (reject booleans, floats, and non-integers)

## 7. Runner — Trials Execution (Phase 2)

- [x] 7.1 In `probe/runner.py`, in `run_suite`, read `task["expect"].get("deterministic", {}).get("trials", 1)` for each task
- [x] 7.2 In `probe/runner.py`, when `trials > 1`, call `run_task` N times for the task; collect all N `{trace, answer}` dicts into a list
- [x] 7.3 In `probe/runner.py`, build the result dict with `"trace"` and `"answer"` from the first trial, and add `"trials": [...]` with all N results when `trials > 1`

## 8. Scorer — Consistency Scoring (Phase 2)

- [x] 8.1 In `probe/scorer.py`, when the result dict contains a `"trials"` key, score each trial independently using the same `det` checks
- [x] 8.2 In `probe/scorer.py`, compute `consistency_score` as the fraction of trials whose PASS/FAIL verdict agrees with the majority verdict; add it to the returned scored dict
- [x] 8.3 In `probe/scorer.py`, for single-trial results (no `"trials"` key), set `consistency_score` to `1.0`

## 9. Reporter — Consistency Column (Phase 2)

- [x] 9.1 In `probe/reporter.py`, check if any scored result has a `consistency_score` field; if so, add a `Consistency` column to the results table
- [x] 9.2 In `probe/reporter.py`, render the consistency cell: `1.0` → `100%` bold green, `0.0` → `0%` bold red, values in between → percentage bold yellow; tasks without `consistency_score` → `—`

## 10. Specs — Phase 2 Delta Applied

- [x] 10.1 Apply delta spec: merge `consistency_score` requirement from `openspec/changes/deterministic-scorers-expansion/specs/scorer/spec.md` into `openspec/specs/scorer/spec.md`
- [x] 10.2 Apply delta spec: merge `trials` validation requirement from `openspec/changes/deterministic-scorers-expansion/specs/loader/spec.md` into `openspec/specs/loader/spec.md`
- [x] 10.3 Apply delta spec: merge `openspec/changes/deterministic-scorers-expansion/specs/runner/spec.md` ADDED requirement (trials support) into `openspec/specs/runner/spec.md`
- [x] 10.4 Apply delta spec: merge `openspec/changes/deterministic-scorers-expansion/specs/reporter/spec.md` into `openspec/specs/reporter/spec.md`
