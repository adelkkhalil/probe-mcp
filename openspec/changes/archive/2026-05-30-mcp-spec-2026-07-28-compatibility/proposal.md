## Why

The MCP 2026-07-28 release candidate removes the `initialize`/`initialized` handshake from the protocol entirely — servers implementing the new spec will fail or hang when they receive an `initialize` message. The current runner calls `await session.initialize()` unconditionally, breaking compatibility with any server targeting the new spec.

## What Changes

- Update `mcp` SDK dependency in `pyproject.toml` to the version that supports the 2026-07-28 stateless protocol (if a newer version is available).
- In `probe/runner.py`, update or remove the `await session.initialize()` call based on how the updated SDK exposes compatibility (remove if no longer needed; wrap in `try/except` if the SDK needs it only for legacy servers).
- Update `openspec/specs/runner/spec.md` to reflect the revised initialization behavior.

## Capabilities

### New Capabilities

_(none — this is a compatibility fix, not a new capability)_

### Modified Capabilities

- `runner`: The handshake requirement changes — `session.initialize()` is no longer unconditionally required. The spec scenario "Server spawns and initializes successfully" and its reference to `session.initialize()` must be updated to reflect the new protocol negotiation behavior.

## Impact

- **`probe/runner.py`**: The `session.initialize()` call on line 138 is modified or removed.
- **`pyproject.toml`**: `mcp` version constraint bumped if a newer SDK version is available.
- **`openspec/specs/runner/spec.md`**: Scenario text updated to remove/revise the `session.initialize()` reference.
- No changes to scorer, reporter, loader, judge, CLI, or example servers — the protocol change is entirely within the runner's session setup.
