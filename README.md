# probe-mcp

Test whether your MCP server actually works.

Most teams building AI agents expose their existing APIs via MCP and assume the agent will figure out the rest. This repo demonstrates why that assumption is wrong, and what to do about it.

---

## What this is

probe-mcp is an eval harness for MCP servers. Point it at your MCP server, give it a set of natural language tasks, and measure whether an agent can complete them correctly.

This repo contains the testbed that motivated the tool: two MCP servers built on top of the classic Northwind commerce database, one raw and one with a semantic layer, with four agent tasks run against both.

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

Three files:

- `northwind_api.py` — the untouchable legacy API, plain Python functions, no MCP decorators
- `mcp_server_raw.py` — naive 1:1 MCP wrap, minimal descriptions, what you get from any OpenAPI-to-MCP generator
- `mcp_server_semantic.py` — semantic layer on top of the same API, rich descriptions, row limits, composite tools, actionable errors

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
| Orders by shipper name | partial fail | pass | Semantic called `shippers()` first. Raw guessed. |
| Overdue orders | partial fail | partial pass | Semantic queried fresh data, reasoned correctly |
| Top employee by orders | fail | partial pass | Raw hit 1MB limit and gave up. Semantic got a partial answer. |

The raw server failed on 3 of 4 tasks. The semantic server passed or partially passed all 4. The only difference was the tool definitions.

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

## Run it yourself

**Requirements:** Python 3.12+, uv

```bash
git clone https://github.com/adelkkhalil/probe-mcp
cd probe-mcp
uv sync
```

Connect to Claude Desktop by adding this to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

Then run the same four tasks against each server and compare what happens. The eval log documents what to look for.

---

## What is coming next

- Automated eval runner — point it at any MCP server, get a score
- Task file format for defining agent eval scenarios
- CI integration so regressions are caught before they ship
- SQL injection detection for MCP servers

---

## Read more

Full write-up with context and analysis: [Your API Works Fine. Your Agent Doesn't.](https://medium.com/@adelkhalil)

---

## License

MIT
