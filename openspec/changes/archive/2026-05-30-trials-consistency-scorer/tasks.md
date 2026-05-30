## 1. Loader — validate trials field

- [x] 1.1 In `probe/loader.py`, add validation for a top-level task `trials` field (alongside `id`, `prompt`, `expect`): must be a positive integer > 0; reject booleans and floats; when absent default to 1; raise `ValueError` identifying the task by id on failure

## 2. Runner — execute N trials

- [x] 2.1 In `probe/runner.py`, read `trials = task.get("trials", 1)` for each task before running
- [x] 2.2 When `trials > 1`, loop `run_task` N times and collect a list of `{trace, answer}` dicts
- [x] 2.3 Store first-trial `trace` and `answer` at the top level of the result dict (backwards compatibility); add a `"trials"` key with the full list of N dicts only when `trials > 1`

## 3. Scorer — compute consistency score

- [x] 3.1 In `probe/scorer.py`, after scoring a result that contains a `"trials"` key, score each trial entry independently using the existing det-check logic
- [x] 3.2 Compute `consistency_score` as the fraction of trials whose status matches the majority status (PASS or FAIL); add it to the scored result dict only when `"trials"` is present
- [x] 3.3 Ensure results without a `"trials"` key have no `consistency_score` field (no change to existing output)

## 4. Reporter — consistency column

- [x] 4.1 In `probe/reporter.py`, detect whether any scored result has a `consistency_score` field; if so, add a `Consistency` column to the Rich table
- [x] 4.2 Render consistency cells: `100%` bold green for 1.0, bold yellow for > 0.5, bold red for ≤ 0.5; `—` for tasks without a score
- [x] 4.3 When `consistency_score` is present and < 0.7, also add a warning message to the task's `failed` list (or a note below the table) indicating the tool description may be too vague

## 5. Example task

- [x] 5.1 In `tasks/northwind.yaml`, add `trials: 3` to at least one existing task (e.g. a `top_customers` or `orders` task) as a working example of the feature

## 6. Spec files — update live specs

- [x] 6.1 Merge the delta spec content from the change directory into `openspec/specs/runner/spec.md` — add the "trials support" requirement if not already present
- [x] 6.2 Merge into `openspec/specs/scorer/spec.md` — add the "consistency_score" requirement if not already present
- [x] 6.3 Merge into `openspec/specs/reporter/spec.md` — add the "consistency column" requirement if not already present
- [x] 6.4 Merge into `openspec/specs/loader/spec.md` — add the "trials must be a positive integer" requirement if not already present
