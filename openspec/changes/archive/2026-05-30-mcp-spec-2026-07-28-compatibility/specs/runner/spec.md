## MODIFIED Requirements

### Requirement: MCP server is spawned as a stdio subprocess

The runner SHALL spawn the MCP server using `StdioServerParameters` with `command` and `args` taken from `suite["server"]` (a dict produced by the loader after resolving `servers.yaml`). The subprocess working directory SHALL be set to `suite["server"]["cwd"]`. The runner SHALL NOT use `sys.executable` or interpret `suite["server"]` as a file path.

#### Scenario: Server spawns using command and args from server config

- **WHEN** `suite["server"]` is `{"command": "uv", "args": ["run", "python", "mcp_server.py"], "cwd": "/project"}`
- **THEN** the subprocess is started with `command="uv"`, `args=["run", "python", "mcp_server.py"]`, and `cwd="/project"`

#### Scenario: Server spawns and session is ready for tool listing

- **WHEN** the resolved command and args refer to a working MCP server (any spec version)
- **THEN** the runner spawns a subprocess, establishes a `ClientSession`, and the session is ready to call `list_tools()` — protocol negotiation (including any initialize handshake required by older servers) is handled by the MCP SDK transparently without an explicit `session.initialize()` call in the runner
