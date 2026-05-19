# probe-mcp

Test whether your MCP server actually works.

Most teams building AI agents expose their existing APIs via MCP and assume the agent will figure out the rest. This repo demonstrates why that assumption is wrong, and what to do about it.

---

## What this is

probe-mcp is an eval harness for MCP servers. Point it at your MCP server, give it a set of natural language tasks, and measure whether an agent can complete them correctly.

This repo contains the testbed that motivated the tool: two MCP servers built on top of the classic Northwind commerce database, one raw and one with a semantic layer, with four agent tasks run against both and an automated eval runner that scores the results.

---

## Architecture

The key insight: the underlying API never changes. The semantic layer sits in front of it and makes the difference.

<table width="100%"><tr><td>

```
┌─────────────────────────────────────────────────┐
│               user / operator                   │
└────────────────────┬────────────────────────────┘
                     │ natural language
                     ▼
┌─────────────────────────────────────────────────┐
│                  AI agent                       │
│     Claude, GPT-4o — reasons over tools         │
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
│   untouchable legacy API — plain Python,        │
│   no MCP decorators, no changes                 │
└─────────────────────────────────────────────────┘
```

</td></tr></table>

Four files:

- `northwind_api.py` — the untouchable legacy API, plain Python functions, no MCP decorators
- `mcp_server_raw.py` — naive 1:1 MCP wrap, minimal descriptions, what you get from any OpenAPI-to-MCP generator
- `mcp_server_semantic.py` — semantic layer on top of the same API, rich descriptions, row limits, composite tools, actionable errors
- `tasks/northwind.yaml` — the eval task suite, four realistic agent tasks with expectations

---

## The experiment

Four realistic agent tasks, run against both servers using Claude Haiku 4.5. Same database, same underlying queries, different tool definitions.

### Raw vs semantic — the difference one docstring makes

| | Raw server | Semantic server |
|---|---|---|
| **Tool name** | `raw_get_orders` | `orders` |
| **Description** | `"Get orders."` | Full context: when to use it, what each param means, ShipVia enum values, NULL semantics, currency |
| **ship_via param** | `int = None` — no explanation | `int = None` — documented as `1=Speedy Express, 2=United Package, 3=Federal Shipping. Call shippers() first.` |
| **limit param** | absent — returns unbounded results | `int = 50` — prevents 1MB crashes |
| **Agent behavior** | Fetched 126 rows, guessed shipper from training knowledge | Called `shippers()` first, used correct filter, database did the work |

One instruction in a docstring changed the entire behavior. The underlying function did not change.

### Results

| Task | Raw server | Semantic server | Key difference |
|------|-----------|-----------------|----------------|
| Customers by country | pass | pass | Baseline — both handle simple lookups |
| Orders by shipper name | partial fail | pass | Semantic called `shippers()` first. Raw guessed from training knowledge. |
| Overdue orders | fail | pass | Raw hit 1MB context limit and crashed. Semantic used limit parameter. |
| Top employee by orders | fail | pass | Raw hit 1MB context limit and crashed. Semantic got a partial answer. |

Raw server: 2/4. Semantic server: 4/4. The only difference was the tool definitions.

Full observations, failure patterns, and root causes are in [eval_log.md](eval_log.md).

---

## What actually makes the difference

None of this required changing the underlying API. Everything that improved agent behavior lived in the tool definitions. Six things matter:

1. **Field naming** — `ShipVia` means nothing to an agent. "Filter by shipper company ID" does.
2. **Enum translation** — an integer with values 1, 2, 3 is a dead end. Documented enums are a lookup table the agent can reason over.
3. **Composite operations** — wrapping multi-step operations into a single intent-shaped tool prevents sequencing errors.
4. **Shaped responses** — agents need only what is actionable. Trimming output reduces noise and misreasoning.
5. **Actionable errors** — "ERR_4471" tells an agent nothing. A plain English explanation with next steps does.
6. **Workflow notes** — which tools should be called first, what the typical sequence is.

---

## The eval runner

probe-mcp ships with an automated eval CLI. It spawns your MCP server as a real subprocess, communicates over the MCP protocol exactly as Claude Desktop does, runs each task through Claude autonomously, and scores the results.

### How it works

```
probe/
  loader.py   — reads task YAML files
  runner.py   — spawns MCP server, runs Claude, captures trace
  scorer.py   — scores trace against expectations
  cli.py      — the probe-mcp command
```

The runner uses the real MCP stdio transport — the same protocol Claude Desktop uses. No mocking, no shortcuts. Claude decides autonomously which tools to call and when.

### Setup

**Requirements:** Python 3.12+, uv, an Anthropic API key

```bash
git clone https://github.com/adelkkhalil/probe-mcp
cd probe-mcp
uv sync
```

Add to your `~/.zshrc`:

```bash
alias probe-mcp="uv run --directory /path/to/probe-mcp python -m probe.cli"
export ANTHROPIC_API_KEY="your-key-here"
```

Reload:

```bash
source ~/.zshrc
```

### Run the eval

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

Against the raw server:

```bash
probe-mcp tasks/northwind.yaml --server mcp_server_raw.py --ignore-tool-names
```

```
Results: 2/4 passed

  ✓ customers_by_country (1 calls)
  ✓ orders_by_shipper (2 calls)
  ✗ overdue_orders (1 calls)
      FAIL: task errored — prompt too long: 215718 tokens > 200000 maximum
  ✗ top_employee (2 calls)
      FAIL: task errored — prompt too long: 215718 tokens > 200000 maximum
```

Same tasks. Same scorer. Same Claude model. Different tool definitions.

### Connect to Claude Desktop

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

### Write your own tasks

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

Expectations:

- `tools_called_includes` — tool names that must appear in the trace
- `max_calls` — maximum number of tool calls (efficiency check)
- `answer_includes` — string that must appear in Claude's final answer

---

## What is coming next

- LLM judge scorer — second Claude call to evaluate answer quality, not just structure
- SQL injection detection — flag MCP servers with unsafe parameter handling
- More task examples — richer scenarios beyond the Northwind baseline
- Support for external APIs via pre-built adapters

---

## Read more

Full write-up with context and analysis: [Your API Works Fine. Your Agent Doesn't.](https://medium.com/@adelkhalil)

---

## License

MIT
