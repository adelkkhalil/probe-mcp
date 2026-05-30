## 1. SDK Inspection

- [x] 1.1 Check the latest available `mcp` SDK version via `uv pip index versions mcp` and review its changelog or source to confirm whether `session.initialize()` is removed, a no-op, or still required for the 2026-07-28 spec
- [x] 1.2 Determine the correct code change for `probe/runner.py`: delete the `await session.initialize()` call, keep it unchanged, or wrap it

## 2. Dependency Update

- [x] 2.1 If the current `mcp>=1.27.1` does not include 2026-07-28 support, bump the version floor in `pyproject.toml` to the minimum version that does
- [x] 2.2 Run `uv sync` to install the updated dependency and confirm no dependency conflicts

## 3. Runner Update

- [x] 3.1 Apply the code change to `probe/runner.py` (line 138: the `await session.initialize()` call) as determined in task 1.2

## 4. Regression Test

- [x] 4.1 Run `uv run python -m probe.cli eval examples/northwind/tasks/northwind.yaml` and confirm all tasks pass (old-spec FastMCP servers still work)

## 5. Spec Update

- [x] 5.1 Update `openspec/specs/runner/spec.md` — replace the "Server spawns and initializes successfully" scenario with the new "Server spawns and session is ready for tool listing" scenario from the delta spec
