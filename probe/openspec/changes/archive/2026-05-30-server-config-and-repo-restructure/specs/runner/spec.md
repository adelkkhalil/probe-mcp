## MODIFIED Requirements

### Requirement: MCP server is spawned as a stdio subprocess

The runner SHALL spawn the MCP server using `StdioServerParameters` with `command` and `args` taken from `suite["server"]` (a dict produced by the loader after resolving `servers.yaml`). The subprocess working directory SHALL be set to `suite["server"]["cwd"]`. The runner SHALL NOT use `sys.executable` or interpret `suite["server"]` as a file path.

#### Scenario: Server spawns using command and args from server config

- **WHEN** `suite["server"]` is `{"command": "uv", "args": ["run", "python", "mcp_server.py"], "cwd": "/project"}`
- **THEN** the subprocess is started with `command="uv"`, `args=["run", "python", "mcp_server.py"]`, and `cwd="/project"`

#### Scenario: Server spawns and initializes successfully

- **WHEN** the resolved command and args refer to a working MCP server
- **THEN** the runner spawns a subprocess and completes the MCP handshake via `session.initialize()`
