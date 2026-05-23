## Context

The scorer reads expectation keys directly from each task's `expect:` dict by string name. Three keys are currently supported: `tools_called_includes`, `max_calls`, and `answer_includes`. The `--ignore-tool-names` flag in the CLI pops `tools_called_includes` by exact string. Task YAML files across `tasks/` hardcode these key names.

## Goals / Non-Goals

**Goals:**
- Rename all three expectation keys to carry the `det_` prefix everywhere they appear (scorer logic, CLI, task YAMLs, specs, README)
- Keep the `--ignore-tool-names` flag name unchanged (it describes user intent, not the key name)

**Non-Goals:**
- Backwards-compatibility shim (no aliasing old key names — they silently produce no checks if left unchanged, which is the right incentive for authors to migrate)
- Any behavior change to scoring logic
- Changes to runner, judge, reporter, loader, or config

## Decisions

**Direct rename with no alias layer**

Old keys that remain in a task YAML after migration are simply unknown to the scorer and produce zero checks — the task will still run but its score will be vacuously PASS. This is intentional: it surfaces migration gaps during the next eval run rather than hiding them behind a compatibility shim that would need its own removal later.

**`det_` prefix over alternatives considered**

| Alternative | Reason rejected |
|---|---|
| `structural_` | Longer; `det` (deterministic) is the standard term in eval literature |
| `check_` | Too generic; doesn't convey the deterministic vs. probabilistic distinction |
| Nested `structural:` block | Requires a parser change and breaks YAML structure; out of scope |

**`--ignore-tool-names` flag pops `det_tools_called_includes`**

The flag name describes user-visible intent (ignore tool name checks), not the internal key. Renaming the flag would be a separate, unrelated change. Only the `pop()` argument changes.

## Risks / Trade-offs

- **Breaking change for task YAMLs** → Mitigation: update all files in `tasks/` as part of this change; any external task files must be migrated manually (document in README)
- **Scorer silently ignores unknown keys** → This is existing behavior, not a regression; the trade-off is accepted

## Migration Plan

1. Rename keys in `probe/scorer.py`
2. Rename `pop()` argument in `probe/cli.py` (two call sites in `eval`, two in `full`)
3. Update inline YAML example in `probe/cli.py` `--help` text
4. Rename keys in `tasks/northwind.yaml` and `tasks/my_server.yaml`
5. Update `openspec/specs/scorer/spec.md` requirement headings and scenario text
6. Update README expectations table

No deployment steps — this is a local CLI tool with no server component.
