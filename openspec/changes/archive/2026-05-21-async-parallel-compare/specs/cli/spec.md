## MODIFIED Requirements

### Requirement: eval --compare runs two servers and prints a comparison table

When `--compare <server>` is passed, the CLI SHALL run the suite against both the primary server and the compare server **concurrently** using independent deep copies of the suite, then print a side-by-side comparison table and individual result tables for both servers. No output is printed until both runs complete.

#### Scenario: --compare produces comparison table and two result tables

- **WHEN** `probe-mcp eval tasks/my_server.yaml --compare other.py` is called
- **THEN** both suites execute simultaneously via `asyncio.gather`
- **THEN** a comparison table with both server names as columns is printed after both complete
- **THEN** individual result tables for each server are printed and two `Saved:` lines are shown

#### Scenario: Output is withheld until both servers finish

- **WHEN** `--compare` is active and one server finishes before the other
- **THEN** no results or tables are printed until both `run_suite` calls have returned

---

### Requirement: full --compare judges both servers after parallel eval

When `full` is called with `--compare`, the CLI SHALL run both eval suites concurrently, then run the judge sequentially on each results file after both evals are complete.

#### Scenario: full --compare judges both servers

- **WHEN** `probe-mcp full tasks/my_server.yaml --compare other.py` is called
- **THEN** both eval suites run concurrently, then the judge is run on each results file in turn
- **THEN** both verdict tables are printed and both `Saved:` paths for judge files are shown
