## MODIFIED Requirements

### Requirement: Tool calls are recorded in the trace

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

### Requirement: trials support runs a task N times when trials > 1

When a task's `expect["deterministic"]` contains `trials` with a value greater than 1, the runner SHALL execute `run_task` exactly N times for that task. Each execution produces an independent `{trace, answer}` result. The aggregated result stored in the results list SHALL contain:

- `"trace"` and `"answer"` from the first trial (for backwards compatibility with the scorer and reporter)
- `"trials"`: a list of N `{trace, answer}` dicts, one per execution

When `trials` is 1 or absent, the runner's output is unchanged (no `"trials"` key added).

#### Scenario: Task with trials: 3 produces three raw results

- **WHEN** `expect["deterministic"]["trials"]` is `3` for a task
- **THEN** the result dict for that task contains a `"trials"` list with exactly 3 entries, each having `"trace"` and `"answer"` keys

#### Scenario: Task without trials produces unchanged result

- **WHEN** `expect["deterministic"]` has no `"trials"` key
- **THEN** the result dict has no `"trials"` key and is structured exactly as before
