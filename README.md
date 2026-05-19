# probe-mcp

An eval harness for MCP servers. Runs a set of natural language tasks against any MCP server, captures the tool call trace, and scores the results against defined expectations.

---

## The problem

When you wrap an existing API as an MCP server, the agent's behavior depends heavily on the quality of the tool definitions, not just the underlying API. Vague descriptions, opaque field names, encoded values, and missing workflow hints all cause agents to fail silently, guess wrong, or crash with context window errors.

There is currently no automated way to measure this. You either run tasks manually in Claude Desktop and observe what happens, or you ship and find out in production.

probe-mcp gives you a test suite for your MCP server.

---

## Use cases

**Before shipping.** Write a set of realistic tasks that represent how agents will use your MCP server. Run them. Find failures before users do.

**After changing tool definitions.** If you improve a docstring, add an enum, or rename a parameter, run the eval again. Confirm the change helped and did not break anything else.

**Comparing raw vs semantic.** Build a naive MCP wrapper and a well-described one. Run the same tasks against both. Measure the difference in pass rate and call efficiency.

**Catching model drift.** A tool definition that worked well with one model version may behave differently after a model update. Run the eval on a schedule to detect regressions.

**Code review for MCP servers.** Use the eval output as evidence in pull requests. A description change that improves pass rate from 2/4 to 4/4 is self-documenting.

---

## Architecture

The underlying API never changes. The semantic layer sits in front of it.

<table width="100%"><tr><td>

```
┌─────────────────────────────────────────────────┐
│               user / operator                   │
└────────────────────┬────────────────────────────┘
                     │ natural language
                     ▼
┌─────────────────────────────────────────────────┐
│                  AI agent                       │
│     any LLM with tool use support               │
└──────────┬──────────────────────────┬───────────┘
           │ MCP tool calls           │ MCP tool calls
           ▼                          ▼
┌──────────────────────┐  ┌───────────────────────────┐
│  mcp_server_raw.py   │  │  mcp_server_semantic.py   │
│  naive 1:1 wrap      │  │  rich descriptions        │
│  fails silently      │  │  guides agent correctly   │
└──────────┬───────────┘  └─────────────┬─────────────┘
           │                            │
           └──────────┬─────────────────┘
                      │ same underlying calls
                      ▼
┌─────────────────────────────────────────────────┐
│               northwind_api.py                  │
│   untouchable legacy API, plain Python,         │
│   no MCP decorators, no changes                 │
└─────────────────────────────────────────────────┘
```

</td></tr></table>

This repo ships four files as a working testbed:

- `northwind_api.py` — the untouchable legacy API, plain Python functions, no MCP decorators
- `mcp_server_raw.py` — naive 1:1 MCP wrap, minimal descriptions, representative of auto-generated wrappers
- `mcp_server_semantic.py` — semantic layer on top of the same API, rich descriptions, row limits, composite tools, actionable errors
- `tasks/northwind.yaml` — four realistic agent tasks with expectations

---

## How the runner works

probe-mcp spawns your MCP server as a subprocess and communicates with it over stdio, the same transport Claude Desktop uses. It then runs each task through a real LLM call with the server's tools attached. Claude decides autonomously which tools to call and when. The runner captures the full trace and scores it against your expectations.

```
probe/
  loader.py   reads task YAML files
  runner.py   spawns MCP server over stdio, runs LLM, captures trace
  scorer.py   scores trace against expectations
  cli.py      the probe-mcp command
```

No mocking. No shortcuts. The eval reflects real agent behavior against a real MCP server.

---

## Setup

**Requirements:** Python 3.12+, uv, an API key for any LLM with tool use support

```bash
git clone https://github.com/adelkkhalil/probe-mcp
cd probe-mcp
uv sync
```

Set your API key. The runner currently uses the Anthropic SDK but the architecture supports any provider. Add to your shell profile or set it in your terminal session:

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Add an alias for convenience. The exact syntax depends on your shell:

```bash
# bash or zsh
alias probe-mcp="uv run --directory /path/to/probe-mcp python -m probe.cli"

# fish
alias probe-mcp="uv run --directory /path/to/probe-mcp python -m probe.cli"
```

Or run it directly without an alias:

```bash
uv run --directory /path/to/probe-mcp python -m probe.cli tasks/northwind.yaml
```

---

## Running the eval

Against the semantic server:

```bash
probe-mcp tasks/northwind.yaml
```

```
Running: customers_by_country
Running: orders_by_shipper
Running: overdue_orders
Running: top_employee

Results: 4/4 passed

  ✓ customers_by_country (1 calls)
      pass: tool 'customers_by_country' was called
      pass: call count 1 within limit 1

  ✓ orders_by_shipper (2 calls)
      pass: tool 'shippers' was called
      pass: tool 'orders' was called
      pass: call count 2 within limit 3
      pass: answer contains 'Speedy Express'

  ✓ overdue_orders (1 calls)
      pass: tool 'orders' was called
      pass: call count 1 within limit 2

  ✓ top_employee (2 calls)
      pass: tool 'employees' was called
      pass: tool 'orders' was called
      pass: call count 2 within limit 5
```

Against the raw server, skipping tool name checks since the raw server uses different names:

```bash
probe-mcp tasks/northwind.yaml --server mcp_server_raw.py --ignore-tool-names
```

```
Results: 2/4 passed

  ✓ customers_by_country (1 calls)
  ✓ orders_by_shipper (2 calls)
  ✗ overdue_orders (1 calls)
      FAIL: task errored, prompt too long: 215718 tokens > 200000 maximum
  ✗ top_employee (2 calls)
      FAIL: task errored, prompt too long: 215718 tokens > 200000 maximum
```

Same tasks, same scorer, same model, different tool definitions.

---

## Writing your own tasks

Task files are YAML. Each task has a prompt and a set of expectations:

```yaml
server: mcp_server_semantic.py

tasks:
  - id: find_orders
    prompt: "Find orders for customer ALFKI shipped via express courier"
    expect:
      tools_called_includes: [shippers, orders]
      max_calls: 3
      answer_includes: "Speedy Express"
```

Available expectations:

- `tools_called_includes` — list of tool names that must appear in the trace
- `max_calls` — maximum number of tool calls allowed (catches inefficient behavior)
- `answer_includes` — string that must appear in the final answer

---

## CLI options

```bash
probe-mcp tasks/northwind.yaml                          # run against server in task file
probe-mcp tasks/northwind.yaml --server other.py        # override the server
probe-mcp tasks/northwind.yaml --ignore-tool-names      # skip tool name checks
```

---

## Connect to Claude Desktop

To explore the servers interactively, add them to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "northwind-raw": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/probe-mcp", "python", "mcp_server_raw.py"]
    },
    "northwind-semantic": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/probe-mcp", "python", "mcp_server_semantic.py"]
    }
  }
}
```

---

## What is coming next

- LLM judge scorer: a second model call to evaluate answer quality beyond structural checks
- SQL injection detection: flag MCP servers with unsafe parameter handling
- Multi-model support: run the same tasks against different LLMs and compare
- More task examples: richer scenarios beyond the Northwind baseline
- Pre-built adapters for third-party APIs

---

## Read more

Full write-up with context and analysis: [Your API Works Fine. Your Agent Doesn't.](https://medium.com/@adelkhalil)

---

## License

MIT
