## Context

The scorer currently reads `tools_called_includes`, `max_calls`, and `answer_includes` directly from the task's flat `expect:` dict. The loader validates those three keys at the top level of `expect:`. The reporter shows a single `Status` column derived from the scorer's result, with no visual distinction between check types. The judge runs as a separate pass and its verdict appears in a separate verdicts table — there is no per-task link in the results table between structural checks and semantic checks.

The result: task authors have no structural way to express "this task requires judging" in the YAML, and the results table conflates what the scorer found with what the judge found.

## Goals / Non-Goals

**Goals:**
- Introduce `expect.deterministic` and `expect.probabilistic` as named sub-dicts in the task YAML schema
- Scorer reads from `expect["deterministic"]` only; no behavior change to individual checks
- Loader validates the new nested structure; emits a deprecation warning (not a hard error) when flat expectation keys are detected at top-level `expect`
- Reporter results table shows `Det` and `Pro` as separate columns alongside the overall `Status`
- Results JSON gains `det_score` and `pro_score` fields (additive, no existing fields removed)
- `tasks/northwind.yaml` migrated to new format

**Non-Goals:**
- New scorer check types (future change)
- Changes to the judge pipeline, runner, config, or CLI
- Hard errors for legacy flat-key task files (warning only, to allow gradual migration)
- Removing or replacing existing results JSON fields

## Decisions

**`expect.deterministic` as the sub-dict key**

Alternatives considered: `structural`, `checks`, `rules`. `deterministic` is the correct term — it means the outcome is fully determined by the trace, with no LLM call. `structural` conflates "nested structure" with "type of check." `checks` is too generic.

**Loader warns on flat keys, does not error**

If the loader raised a hard error, every task file would have to be migrated before the new code could run at all. A warning lets the scorer proceed with zero deterministic checks (surfacing the migration gap at score time), while still signaling to the author that the format is wrong. A future change can promote the warning to an error after migration is complete.

**`det_score` / `pro_score` added to scored result, existing fields untouched**

The reporter needs structured access to pass/total counts and pro verdict separately. Adding `det_score: {passed: N, total: M}` and `pro_score: "PASS" | "FAIL" | null` as new optional fields is backward compatible: existing consumers of the results JSON see new keys they can ignore. No existing field is removed or renamed.

**`--ignore-tool-names` pops from `expect["deterministic"]`, not top-level**

The flag's purpose is to strip tool-name checks before the run. After this change, those checks live in `expect["deterministic"]["tools_called_includes"]`. The pop must move to the nested dict; the flag name and behavior remain identical from the user's perspective. This is an implementation detail, not a behavior change.

**Reporter: add `Det` and `Pro` columns, keep `Calls` column**

`Calls` (raw trace length) is independently useful for debugging — it doesn't duplicate the det score. `Det` shows `N/M passed` (check pass ratio). `Pro` shows `PASS (judge)`, `FAIL (judge)`, or `—` when no `probabilistic` section was declared. The overall `Status` column is derived from `det_score` alone (probabilistic is advisory; the scorer does not know the judge verdict at score time).

## Risks / Trade-offs

- **[Risk] Task YAMLs not migrated produce silently vacuous scores** → Mitigation: loader emits a named warning at load time that prints to stderr; the score will show `det: 0/0` making the gap visible in the reporter
- **[Risk] `--ignore-tool-names` silently stops working if pop targets wrong key** → Mitigation: flag must be updated atomically with the scorer change; covered by a task item
- **[Risk] Reporter column width increases** → Known trade-off; Rich auto-fits columns, and the table already truncates answers

## Migration Plan

1. Update loader to validate new nested structure and emit warning on flat keys
2. Update scorer to read from `expect.get("deterministic", {})`; populate `det_score` / `pro_score` in result
3. Update `--ignore-tool-names` pop target in `probe/cli.py`
4. Update reporter to render `Det` and `Pro` columns from `det_score` / `pro_score`
5. Migrate `tasks/northwind.yaml` to new format
6. Update specs and README

No deployment steps — local CLI only. Rollback: revert the six files changed.
