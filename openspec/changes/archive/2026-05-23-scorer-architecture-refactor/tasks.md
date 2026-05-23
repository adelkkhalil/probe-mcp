## 1. Loader — Nested Structure Validation

- [x] 1.1 In `probe/loader.py`, add validation that `expect["deterministic"]` is a dict when present; raise `ValueError` naming the task id if not
- [x] 1.2 In `probe/loader.py`, add validation that `expect["probabilistic"]` is a dict when present; raise `ValueError` naming the task id if not
- [x] 1.3 In `probe/loader.py`, add validation that `expect["probabilistic"]["judge"]` is a boolean when present; raise `ValueError` for non-boolean values
- [x] 1.4 In `probe/loader.py`, move the three existing key checks (`tools_called_includes`, `max_calls`, `answer_includes`) to read from `expect.get("deterministic", {})` instead of `expect`
- [x] 1.5 In `probe/loader.py`, add a deprecation warning path: if `expect` contains any of the three legacy flat keys at top level, emit a `UserWarning` naming the task id and the offending keys (do not raise an error)

## 2. Scorer — Read from Nested Dict

- [x] 2.1 In `probe/scorer.py`, change the top of `score_task` to extract `det = result["expect"].get("deterministic", {})` and use `det` in place of `expect` for all three key lookups (`tools_called_includes`, `max_calls`, `answer_includes`)
- [x] 2.2 In `probe/scorer.py`, after evaluating all checks, compute `det_score = {"passed": len(passed), "total": len(passed) + len(failed)}` (before short-circuit error path, so error results get `det_score: {"passed": 0, "total": 0}`)
- [x] 2.3 In `probe/scorer.py`, compute `pro_score`: if `result["expect"].get("probabilistic", {}).get("judge") is True` set to `"pending"`, else `None`
- [x] 2.4 In `probe/scorer.py`, include `det_score` and `pro_score` in the returned scored dict for both error and non-error paths

## 3. CLI — Fix --ignore-tool-names Flag

- [x] 3.1 In `probe/cli.py`, update all four `pop("tools_called_includes", None)` calls in the `eval` and `full` commands to pop from `task["expect"].get("deterministic", {})` instead of `task["expect"]`

## 4. Reporter — Det and Pro Columns

- [x] 4.1 In `probe/reporter.py`, add a `Det` column to the results table; populate it from `result.get("det_score", {})` as `"N/M"` (e.g., `"2/3"`)
- [x] 4.2 In `probe/reporter.py`, add a `Pro` column to the results table; populate it from `result.get("pro_score")`: `null` → `"—"`, `"pending"` → `"—"`, a resolved judge verdict string → styled `"PASS (judge)"` / `"FAIL (judge)"` etc.
- [x] 4.3 In `probe/reporter.py`, if `print_results` receives an optional `verdicts` dict (keyed by task id), use it to resolve `"pending"` pro scores to actual judge verdicts for display

## 5. Task YAML Migration

- [x] 5.1 In `tasks/northwind.yaml`, restructure all four tasks' `expect:` blocks: move `tools_called_includes`, `max_calls`, `answer_includes` under `expect.deterministic:`, and add `expect.probabilistic: {judge: true}` to tasks that benefit from judging
- [x] 5.2 If `tasks/my_server.yaml` exists, apply the same migration

## 6. Specs and Documentation

- [x] 6.1 Apply delta specs: merge `openspec/changes/scorer-architecture-refactor/specs/scorer/spec.md` into `openspec/specs/scorer/spec.md`
- [x] 6.2 Apply delta specs: merge `openspec/changes/scorer-architecture-refactor/specs/loader/spec.md` into `openspec/specs/loader/spec.md`
- [x] 6.3 Apply delta specs: merge `openspec/changes/scorer-architecture-refactor/specs/reporter/spec.md` into `openspec/specs/reporter/spec.md`
- [x] 6.4 In `README.md`, update the task authoring / expectations section to show the new nested `deterministic:` / `probabilistic:` YAML format and remove references to the flat key format
