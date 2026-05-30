## MODIFIED Requirements

### Requirement: Tool use blocks are dispatched back through the MCP session

When the API response has `stop_reason == "tool_use"`, the runner SHALL dispatch each `tool_use` block to `session.call_tool` and append the tool result to the message history before the next iteration. Each trace entry SHALL record the tool name, input parameters, and whether the tool call returned an error (`"error": bool`).

#### Scenario: Tool calls are recorded in the trace with error flag

- **WHEN** the model issues a tool call during a task
- **THEN** the trace list gains an entry `{"tool": <name>, "params": <input>, "error": <bool>}` for each dispatched call, where `"error"` reflects `result.isError` from the MCP session

#### Scenario: Successful tool call records error as false

- **WHEN** `session.call_tool` returns a result with `isError == False`
- **THEN** the trace entry for that call has `"error": false`

#### Scenario: Failed tool call records error as true

- **WHEN** `session.call_tool` returns a result with `isError == True`
- **THEN** the trace entry for that call has `"error": true`

---

## ADDED Requirements

### Requirement: run_suite prints a Running: line for each task and mirrors it to log_console when provided

For each task in the suite, `run_suite` SHALL print `Running: {task_id}` using a Rich Console before invoking `run_task`. When called with a non-None `log_console` parameter, this line SHALL also be written to `log_console`. When `log_console` is `None`, output goes only to the terminal console.

#### Scenario: Running: line appears in log file when log_console is provided

- **WHEN** `run_suite(suite, tasks_file, log_console=lc)` is called
- **THEN** each `Running: <task_id>` line is written to both the terminal console and `lc`

#### Scenario: run_suite is unchanged when log_console is None

- **WHEN** `run_suite(suite, tasks_file)` is called without `log_console`
- **THEN** `Running:` lines go only to the terminal console, identical to previous behaviour
