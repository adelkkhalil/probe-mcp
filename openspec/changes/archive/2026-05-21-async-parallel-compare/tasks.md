## 1. Update eval command

- [x] 1.1 Add `import asyncio` to `probe/cli.py` (check if already present)
- [x] 1.2 In the `eval` command handler, replace the two sequential `_run_async(run_suite(...))` calls inside the `if compare:` branch with a single `_run_async(asyncio.gather(run_suite(suite, ...), run_suite(suite2, ...)))` call
- [x] 1.3 Unpack the gather result as `(results, results_file), (results2, results2_file)` and verify the rest of the compare branch (scoring, printing, Saved lines) is unchanged

## 2. Update full command

- [x] 2.1 In the `full` command handler, apply the same `asyncio.gather` replacement for the `if compare:` branch eval phase
- [x] 2.2 Verify the judge phase (which runs sequentially after both evals) is unaffected and still receives `results_file` and `results2_file` correctly

## 3. Verify behavior

- [x] 3.1 Run `probe-mcp eval <suite> --compare <other>` and confirm both result files are written and the comparison table plus both individual tables appear correctly
- [x] 3.2 Run `probe-mcp full <suite> --compare <other>` and confirm both result files, both judge files, both verdict tables, and all `Saved:` lines are present
- [x] 3.3 Run a non-compare `probe-mcp eval <suite>` to confirm the single-server path is unaffected
