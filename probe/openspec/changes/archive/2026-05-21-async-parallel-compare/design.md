## Context

The `eval` and `full` CLI commands currently handle `--compare` by calling `_run_async(run_suite(...))` twice in sequence. `_run_async` wraps `asyncio.run`, so each call starts and completes its own event loop before the next begins. Since `run_suite` is already a fully async function (MCP stdio transport, async Anthropic client), there is no I/O blocking preventing the two from running side by side.

## Goals / Non-Goals

**Goals:**
- Run both `run_suite` coroutines concurrently using `asyncio.gather` inside a single `asyncio.run` call.
- Preserve the existing output ordering: comparison table → primary results → compare results.
- Keep the results file naming convention, content format, and all downstream judge/report behavior identical.
- Apply the change in `eval` and `full`; non-compare paths are untouched.

**Non-Goals:**
- Parallelizing the tasks *within* a single suite (each suite's tasks still run sequentially inside `run_suite`).
- Changing `run_suite` or any module other than `cli.py`.
- Adding concurrency to the judge phase.
- Streaming partial results before both suites finish.

## Decisions

**Replace two `_run_async` calls with one `asyncio.gather`**

Current pattern in both `eval` and `full`:
```python
results, results_file = _run_async(run_suite(suite, tasks_file, verbose=verbose))
# ... first server output ...
results2, results2_file = _run_async(run_suite(suite2, tasks_file, verbose=verbose))
```

New pattern:
```python
(results, results_file), (results2, results2_file) = _run_async(
    asyncio.gather(
        run_suite(suite, tasks_file, verbose=verbose),
        run_suite(suite2, tasks_file, verbose=verbose),
    )
)
```

`_run_async` already calls `asyncio.run`, so a single call with `asyncio.gather` is all that's needed — no new helpers required.

**Why `asyncio.gather` over `asyncio.TaskGroup` or `concurrent.futures`**

`asyncio.gather` is the simplest fit: both coroutines are already async, the number of coroutines is fixed at two, and gather returns results in input order which preserves the deterministic output ordering requirement. `asyncio.TaskGroup` (Python 3.11+) is semantically equivalent but more verbose for this case. `concurrent.futures` would add a thread pool for no benefit since the bottleneck is I/O, not CPU.

**Output is held until both complete**

`asyncio.gather` awaits all coroutines before returning, so all printing of tables and `Saved:` lines happens after both suites finish. This is the correct behavior: the comparison table requires both scored lists.

**Verbose print-during-run is preserved**

`run_suite` prints `"Running: <task_id>"` lines as each task executes. With `asyncio.gather`, these lines from both servers will be interleaved in the terminal. This is acceptable — the verbose flag is already opt-in, and interleaved progress lines are a natural consequence of parallelism.

## Risks / Trade-offs

[Interleaved progress lines] → Low severity. The `"Running: <task_id>"` lines from both servers will appear interleaved during a `--compare` run. No mitigation needed — the final output tables are unaffected.

[Failure in one gather branch] → If one `run_suite` raises (e.g. server file not found), `asyncio.gather` propagates the first exception and the other branch may be cancelled. This matches the current behavior where the first `_run_async` call fails and the second never runs. The `_run_async` wrapper already converts `FileNotFoundError`/`ValueError` to `ClickException`, so error display is unchanged.

[MCP stdio resource contention] → Each `run_suite` spawns a separate subprocess with its own stdio pipes. There is no shared state between the two runs. No contention risk.

## Migration Plan

1. Update `eval` command handler in `probe/cli.py`: replace the two sequential `_run_async(run_suite(...))` calls inside the `if compare:` branch with a single `asyncio.gather`.
2. Update `full` command handler in `probe/cli.py`: same change for the compare branch.
3. Add `import asyncio` to `cli.py` if not already present.
4. Manual smoke test: `probe-mcp eval <suite> --compare <other>` and `probe-mcp full <suite> --compare <other>`.

No rollback strategy needed — the change is contained to two call sites in one file and is trivially reversible.

## Open Questions

None. The approach is straightforward and fully contained within `cli.py`.
