## Context

The scorer reads from `expect["deterministic"]` and currently supports three checks (`tools_called_includes`, `max_calls`, `answer_includes`). The trace format stored by the runner is `[{"tool": name, "params": input}, ...]` — it does not currently record whether a tool call returned an error. The loader validates the three existing keys. The reporter has no concept of multi-run consistency.

## Goals / Non-Goals

**Goals:**
- Add six new deterministic checks in Phase 1, all reading from `expect["deterministic"]`
- Extend the runner trace format to include an `"error": bool` field per entry (required by `no_error`)
- Add trials consistency scoring in Phase 2 with minimal changes to the existing result structure
- Keep all changes additive — no existing check behavior, result file format, or CLI surface changes

**Non-Goals:**
- LLM-based checks (those belong in the judge pipeline)
- Changing the result file naming convention or `meta` structure
- Nested lists of `tool_params_include` checks per task (single dict per task; future extension if needed)
- Collecting trial answers for similarity scoring (Phase 2 uses PASS/FAIL status agreement, not answer text comparison)

## Decisions

**`tool_params_include` checks parameter keys, not values**

Tool call values are semantic (the right city name, the right account number). Whether the right keys were used is structural. Checking values would require encoding the expected value in the YAML, making tasks brittle and LLM-non-deterministic. Checking presence of keys is sufficient to assert the agent used the correct API surface.

**`tool_params_include`: any call to the named tool satisfies the check**

If the agent calls the same tool multiple times (e.g., with different filters), the check passes if ANY call includes all listed parameter keys. This is consistent with `tools_called_includes` semantics.

**`tools_called_sequence` is a subsequence match, not a consecutive-window match**

`[tool_a, tool_b]` passes if `tool_a` appears anywhere before `tool_b` in the trace — other tools may appear between them. A consecutive-match requirement would be overly brittle and would fail on agents that do exploratory calls between the required ones.

**`no_error` requires extending the trace format**

The runner currently stores only `{"tool": name, "params": input}` per trace entry. Whether a tool call errored is a structural property of the execution that `no_error` needs. Adding `"error": bool` to each trace entry is the minimal additive change — existing consumers see a new key they can ignore, and the scorer can read it. The runner sets `"error": result.isError` using the `isError` field already returned by `session.call_tool`.

**Phase 2: trials result stored as `"trials": [{trace, answer}, ...]` on the result dict**

When `trials > 1`, the runner calls `run_task` N times for the same task. The aggregated result keeps the first trial's `trace` and `answer` at the top level (preserving backwards compatibility with the existing scorer and reporter) and adds a `"trials"` list with all N raw `{trace, answer}` dicts. The scorer reads `"trials"` to compute the consistency score.

**Phase 2: consistency score = fraction of trials with same PASS/FAIL verdict as the majority**

Simpler alternatives (exact answer match, semantic similarity) either over-count noise or require an LLM call. Status-agreement captures the signal of interest: does the agent reliably produce a passing result, or does it sometimes fail? A score of 1.0 means all trials agree; 0.5 means half agree.

## Risks / Trade-offs

- **[Risk] `tool_params_include` is a single dict; tasks needing param checks on two tools need two separate tasks** → Accepted trade-off for simplicity; document clearly
- **[Risk] Adding `"error"` to trace entries changes the JSON schema of results files** → Additive change only; existing readers ignore unknown keys
- **[Risk] Phase 2 trials multiply API cost N×** → Opt-in only, user sets `trials`; document cost implication
- **[Risk] `tools_called_sequence` with an empty list trivially passes** → Defined behaviour; loader should warn if list is empty

## Migration Plan

Phase 1 (scorer + loader + runner trace + task YAMLs):
1. Extend runner to set `"error": result.isError` on each trace entry
2. Add six check blocks to `score_task()` in scorer
3. Add validation for six new keys in loader
4. Update `tasks/northwind.yaml` with examples; add new UAE/e-commerce YAML examples

Phase 2 (trials):
1. Runner: when `trials > 1`, loop `run_task` N times, store all results under `"trials"` key
2. Scorer: new `score_consistency()` function; scorer reads `"trials"` from result if present
3. Reporter: detect `"consistency_score"` in scored results, add Consistency column if any task has it

No deployment steps. Rollback: revert the changed files.
