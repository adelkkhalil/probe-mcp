## Context

The probe-mcp eval harness currently runs each task exactly once. A single run cannot distinguish between a tool description that is reliably clear and one that produces inconsistent results by chance. Adding a `trials` field lets users re-run the same task N times and measure how often the agent reaches the same conclusion — a direct signal of tool-description quality.

The existing pipeline is: loader → runner → scorer → reporter. Trials touches all four modules but each change is additive. Backwards compatibility is maintained by making `trials` optional (default 1) and only adding the `"trials"` key and `consistency_score` field when N > 1.

## Goals / Non-Goals

**Goals:**
- Per-task `trials: N` field; N independent runs; `"trials"` array in results JSON
- Consistency score = fraction of trials matching the majority verdict (PASS/FAIL)
- Consistency column in the reporter table when any task uses trials
- Zero change to single-trial behaviour (existing task files need no edits)

**Non-Goals:**
- Semantic similarity comparison of answer text (simple majority-verdict fraction is sufficient for v1)
- Parallel trial execution (sequential keeps the implementation minimal)
- Per-trial judge invocation (the judge runs once on the first-trial answer)
- CLI flags to control trials count globally

## Decisions

**Where `trials` lives in the task schema** — top-level task field alongside `id`, `prompt`, and `expect`, rather than inside `expect.deterministic`.
A top-level field is the right level of abstraction: trials controls how many times a task runs, which is a property of the task itself, not a structural assertion about the agent's behaviour. Nesting it inside `deterministic` would imply it is a check like `max_calls` or `tools_called_includes`, which it is not. It also keeps the loader validation path clear — `trials` is validated alongside the other task-level fields, not inside the expect-dict traversal.

**Consistency score algorithm** — majority-verdict fraction (count of trials matching the most common PASS/FAIL verdict, divided by N).
This is simple, deterministic, and matches the mental model: "what fraction of runs agree?" The alternative (pairwise text similarity) would require a fuzzy-match library and introduces a tuning knob that is not needed for the initial signal.

**First-trial answer as the canonical answer** — `result["answer"]` and `result["trace"]` always come from trial 0; all N `{trace, answer}` dicts are preserved under `result["trials"]`.
This keeps the scorer's existing deterministic checks (which read `result["answer"]` and `result["trace"]`) working without any changes. The consistency score is computed separately from the per-trial results.

**Scorer computes consistency, not the runner** — the scorer reads the `"trials"` array and adds `consistency_score`.
Keeps the runner's responsibility narrow (execute tasks, record raw results) and the scorer's responsibility consistent (all scoring logic lives in one place).

**Det checks run on every trial independently** — each trial's trace/answer is scored; the majority result drives consistency.
This gives the most informative signal: if 2/3 trials pass all det checks, consistency is 0.67. Running det checks only on the first trial would miss cross-trial variance.

## Risks / Trade-offs

[Cost] N trials = N real API calls per task → runs can become expensive. Mitigation: `trials` defaults to 1, so existing suites are unaffected. Users opt in explicitly per task.

[Verbosity] N MCP server subprocesses are spawned per task when trials > 1 → longer runtime. Mitigation: sequential execution is simpler and each subprocess is short-lived; parallelism can be added later.

[Backward compatibility] Results JSON gains a `"trials"` key for multi-trial tasks and scored results gain `consistency_score`. Mitigation: both fields are only present when N > 1, so existing result files and tooling are unaffected.

## Migration Plan

No migration needed. `trials` is an opt-in field; existing task files work unchanged. New results files are a strict superset of the old schema.
