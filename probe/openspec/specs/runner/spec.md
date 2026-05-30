# Spec: Runner

## Purpose

The runner spawns an MCP server as a stdio subprocess, fetches its tool list, drives an agent loop via the Anthropic API, captures a tool-call trace, and saves results to a JSON file. No mocking is used — the MCP protocol and API calls are real.

## Requirements

### Requirement: MCP server is spawned as a stdio subprocess

The runner SHALL spawn the MCP server using `StdioServerParameters` with `command` and `args` taken from `suite["server"]` (a dict produced by the loader after resolving `servers.yaml`). The subprocess working directory SHALL be set to `suite["server"]["cwd"]`. The runner SHALL NOT use `sys.executable` or interpret `suite["server"]` as a file path.

#### Scenario: Server spawns using command and args from server config

- **WHEN** `suite["server"]` is `{"command": "uv", "args": ["run", "python", "mcp_server.py"], "cwd": "/project"}`
- **THEN** the subprocess is started with `command="uv"`, `args=["run", "python", "mcp_server.py"]`, and `cwd="/project"`

#### Scenario: Server spawns and initializes successfully

- **WHEN** the resolved command and args refer to a working MCP server
- **THEN** the runner spawns a subprocess and completes the MCP handshake via `session.initialize()`

---

### Requirement: Tool list is fetched from the MCP server

After initializing the session, the runner SHALL call `session.list_tools()` and convert the result into Anthropic tool format (with `name`, `description`, and `input_schema` keys) before running any tasks.

#### Scenario: Tools are converted to Anthropic format

- **WHEN** the MCP server advertises tools with names and schemas
- **THEN** each tool in the runner's tool list has `"name"`, `"description"`, and `"input_schema"` keys

---

### Requirement: Agent loop calls the Anthropic API

For each task the runner SHALL call `anthropic.messages.create` with the model from config, the max_tokens from config, the server's tool list, and the accumulated message history.

#### Scenario: API call uses configured model and token limit

- **WHEN** running a task
- **THEN** `client.messages.create` is called with `model=get_agent_model(config)` and `max_tokens=get_max_tokens(config)`

---

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

### Requirement: run_suite prints a Running: line for each task and mirrors it to log_console when provided

For each task in the suite, `run_suite` SHALL print `Running: {task_id}` using a Rich Console before invoking `run_task`. When called with a non-None `log_console` parameter, this line SHALL also be written to `log_console`. When `log_console` is `None`, output goes only to the terminal console.

#### Scenario: Running: line appears in log file when log_console is provided

- **WHEN** `run_suite(suite, tasks_file, log_console=lc)` is called
- **THEN** each `Running: <task_id>` line is written to both the terminal console and `lc`

#### Scenario: run_suite is unchanged when log_console is None

- **WHEN** `run_suite(suite, tasks_file)` is called without `log_console`
- **THEN** `Running:` lines go only to the terminal console, identical to previous behaviour

---

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

---

### Requirement: Iteration cap prevents infinite loops

The agent loop SHALL terminate with an error result after `MAX_ITERATIONS` (20) loop turns if `end_turn` has not been reached, rather than looping indefinitely.

#### Scenario: Exceeding max iterations returns error answer

- **WHEN** the agent calls tools on every iteration and never reaches `end_turn` within 20 turns
- **THEN** `run_task()` returns an answer equal to `"ERROR: agent exceeded max iterations (20)"`

---

### Requirement: Unexpected stop reasons return error results

If the API returns a `stop_reason` that is neither `"end_turn"` nor `"tool_use"`, the runner SHALL return an error result without continuing the loop.

#### Scenario: Early stop reason yields error answer

- **WHEN** `response.stop_reason` is neither `"end_turn"` nor `"tool_use"`
- **THEN** `run_task()` returns an answer starting with `"ERROR: agent stopped early"`

---

### Requirement: API exceptions return error results

If `anthropic.messages.create` raises an exception, the runner SHALL catch it and return an answer prefixed with `"ERROR:"` containing the truncated exception message, rather than propagating the exception.

#### Scenario: API exception yields error answer

- **WHEN** `client.messages.create` raises an exception
- **THEN** `run_task()` returns `{"trace": <partial_trace>, "answer": "ERROR: <message>"}` without raising

---

### Requirement: tool_use response with no tool blocks returns error

If `stop_reason == "tool_use"` but the response contains no `tool_use` content blocks, the runner SHALL return an error result immediately.

#### Scenario: Empty tool_use blocks yields error

- **WHEN** `stop_reason == "tool_use"` and no `tool_use` blocks are present in the response
- **THEN** `run_task()` returns an answer containing `"ERROR: response had stop_reason=tool_use but contained no tool_use blocks"`

---

### Requirement: Final answer must be a text block

After `end_turn`, the runner SHALL extract the first text content block as the final answer. If no text block is present, it SHALL return an error result.

#### Scenario: No text block at end_turn returns error

- **WHEN** the model stops with `end_turn` but produces no text content block
- **THEN** `run_task()` returns an answer starting with `"ERROR: agent ended without producing a text response"`

---

### Requirement: FastMCP log noise is suppressed by default

Unless `verbose=True` is passed, the runner SHALL set `FASTMCP_SHOW_SERVER_BANNER=false` and `FASTMCP_LOG_LEVEL=WARNING` in the subprocess environment.

#### Scenario: Default mode suppresses FastMCP output

- **WHEN** `run_suite(suite, verbose=False)` is called
- **THEN** the subprocess environment has `FASTMCP_SHOW_SERVER_BANNER=false` and `FASTMCP_LOG_LEVEL=WARNING`

#### Scenario: Verbose mode does not suppress FastMCP output

- **WHEN** `run_suite(suite, verbose=True)` is called
- **THEN** the runner does not set `FASTMCP_SHOW_SERVER_BANNER` or `FASTMCP_LOG_LEVEL` in the subprocess environment

---

### Requirement: Results file is saved with a deterministic naming convention

After all tasks complete, the runner SHALL save a JSON results file to the configured results directory. The filename MUST follow the pattern `{server_stem}_{timestamp}_{agent_model}_{run_id}.json` where `run_id` is a 4-character hex token and timestamp is `YYYY-MM-DD_HH-MM`.

#### Scenario: Results file name follows the convention

- **WHEN** `run_suite()` completes successfully
- **THEN** a file is created in `get_results_dir(config)/` whose name matches `<server_stem>_<YYYY-MM-DD_HH-MM>_<model>_<4hex>.json`

#### Scenario: Results file contains meta and results

- **WHEN** the results file is read back from disk
- **THEN** it contains a `"meta"` object with `server`, `tasks_file`, `agent_model`, `timestamp`, and `run_id` keys
- **THEN** it contains a `"results"` list with one entry per task

---

### Requirement: Results directory is created if absent

The runner SHALL create the results directory (including any parent directories) if it does not already exist before writing the results file.

#### Scenario: Missing results directory is created automatically

- **WHEN** the configured results directory does not exist
- **THEN** `run_suite()` creates the directory and writes the file successfully
