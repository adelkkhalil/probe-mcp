## Context

The runner uses `mcp.ClientSession` over a stdio transport. After entering the session context manager, it explicitly calls `await session.initialize()` to perform the MCP protocol handshake before listing tools. This call sends an `initialize` request and waits for an `initialized` notification, which is how MCP has worked up to and including the 2025-x specs.

The MCP 2026-07-28 release candidate removes the `initialize`/`initialized` exchange entirely — the protocol becomes stateless from the start. An SDK updated for this spec handles the version negotiation automatically (or omits it), making an explicit `session.initialize()` call either a no-op, deprecated, or absent from the public API.

Current state:
- `pyproject.toml`: `mcp>=1.27.1`
- `probe/runner.py` line 138: `await session.initialize()`

## Goals / Non-Goals

**Goals:**
- Servers implementing MCP 2026-07-28 (stateless) connect and run tasks correctly.
- Servers implementing earlier MCP specs continue to work without changes.
- The runner's code change is minimal and localized to session setup.

**Non-Goals:**
- Tasks extension support (separate phase).
- Changes to any component outside runner setup (scorer, reporter, loader, judge, CLI).
- Supporting MCP transports other than stdio.

## Decisions

### Decision: Follow the SDK — don't re-implement protocol detection

**Rationale**: The SDK is responsible for protocol negotiation; the runner should not try to detect which spec the server implements and branch accordingly. If the updated SDK makes `session.initialize()` a no-op for new-spec servers and still required for old-spec servers, the existing call can stay as-is. If the SDK removes `initialize()` from the public API entirely (the SDK now negotiates internally), the call is deleted. The implementation task begins by reading the installed SDK source/changelog to confirm which case applies before writing code.

**Alternatives considered**:
- Wrap in `try/except AttributeError` — fragile; attributes don't disappear silently in well-maintained SDKs.
- Version-sniff the server and branch — couples runner to protocol version detection, adds complexity the SDK already handles.

### Decision: Bump mcp lower bound only if necessary

**Rationale**: Only raise the `mcp>=` version floor if the current version (`1.27.1`) does not include 2026-07-28 support. Unnecessary bumps constrain adopters and may pull in unrelated breaking changes. The implementation task checks `uv pip index versions mcp` and the SDK changelog before deciding.

## Risks / Trade-offs

- **[Risk] SDK inspection required before coding** → The exact code change (remove call, keep call, or try/except) depends on the installed SDK version's behavior. This is resolved in the first implementation task before any file is edited.
- **[Risk] Northwind example servers use FastMCP, which may lag the SDK** → The Northwind servers are legacy targets; they implement an older protocol. Confirm they still pass the Northwind eval after any change — this is the regression gate.
- **[Risk] fastmcp version constraint** → `fastmcp>=3.3.1` (used by example servers) and `mcp>=X` (used by the runner) are independent packages. A bump in `mcp` does not force a bump in `fastmcp`. No cross-constraint changes are expected.

## Migration Plan

1. Inspect updated SDK to determine required code change (runner.py).
2. Edit `probe/runner.py` accordingly (one-line change at most).
3. Bump `mcp` version in `pyproject.toml` if needed; run `uv sync`.
4. Run `uv run python -m probe.cli eval examples/northwind/tasks/northwind.yaml` to confirm old-spec servers still pass.
5. Update `openspec/specs/runner/spec.md` to drop/revise the `session.initialize()` reference.

Rollback: revert `pyproject.toml` and `runner.py` to prior state; re-run `uv sync`.

## Open Questions

- Which exact `mcp` version introduces 2026-07-28 support? (Resolved during implementation task 1.)
- Does the updated SDK keep `session.initialize()` as a no-op or remove it? (Resolved during implementation task 1.)
