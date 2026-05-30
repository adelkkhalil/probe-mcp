## ADDED Requirements

### Requirement: Compare suites run concurrently

When `--compare` is active, the CLI SHALL execute both `run_suite` calls concurrently via `asyncio.gather` so that neither server waits for the other to finish before it starts.

#### Scenario: Both servers start before either finishes

- **WHEN** `probe-mcp eval tasks/suite.yaml --compare other.py` is called
- **THEN** both MCP server subprocesses are spawned and processing tasks simultaneously, not sequentially

#### Scenario: Results are collected after both complete

- **WHEN** both suite runs finish
- **THEN** the CLI collects results from both runs at the same time and proceeds to scoring and display

---

### Requirement: Parallel compare produces independent result files

Each compare run SHALL produce its own results file with its own `run_id` and timestamp, exactly as in the non-parallel (sequential) case. The parallelism SHALL NOT affect file naming or content format.

#### Scenario: Two result files written after parallel compare

- **WHEN** `--compare` is used and both suites complete
- **THEN** two separate results JSON files are written, one per server, each with its own `run_id` and timestamp

#### Scenario: File naming convention is preserved

- **WHEN** both suites complete
- **THEN** each file name follows the pattern `{server_stem}_{timestamp}_{agent_model}_{run_id}.json`

---

### Requirement: Parallel compare output order matches primary-then-compare

The display output from a parallel compare run SHALL follow the same ordering as the sequential case: comparison table first, then primary server results, then compare server results.

#### Scenario: Output order is deterministic regardless of which server finished first

- **WHEN** the compare server finishes before the primary server
- **THEN** the comparison table, primary server table, and compare server table are still printed in that order
