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

This repo ships a working testbed built on the classic Northwind commerce database:

- `northwind_api.py` — the untouchable legacy API, plain Python functions, no MCP decorators
- `mcp_server_raw.py` — naive 1:1 MCP wrap, minimal descriptions, representative of auto-generated wrappers
- `mcp_server_semantic.py` — semantic layer on top of the same API, rich descriptions, row limits, composite tools, actionable errors
- `tasks/northwind.yaml` — four realistic agent tasks with expectations

---

## How it works

probe-mcp spawns your MCP server as a subprocess and communicates with it over stdio, the same transport Claude Desktop uses. It then runs each task through a real LLM call with the server's tools attached. The LLM decides autonomously which tools to call and when. The runner captures the full trace and scores it against your expectations.

```
probe/
  config.py     reads probe.yaml, resolves model names
  loader.py     reads task YAML files
  runner.py     spawns MCP server over stdio, runs LLM, captures trace
  scorer.py     scores trace against expectations
  reporter.py   formats and prints results using Rich
  judge.py      evaluates saved results using a second LLM call
  cli.py        the probe-mcp commands
```

No mocking. No shortcuts. The eval reflects real agent behavior against a real MCP server.

---

## Setup

**Requirements:** Python 3.12+, uv, an Anthropic API key

```bash
git clone https://github.com/adelkkhalil/probe-mcp
cd probe-mcp
uv sync
```

Set your API key:

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Add an alias to your shell profile:

```bash
alias probe-mcp="uv run --directory /path/to/probe-mcp python -m probe.cli"
```

Or run directly without an alias:

```bash
uv run --directory /path/to/probe-mcp python -m probe.cli [command]
```

---

## Commands

```bash
probe-mcp help     Show workflow guide and all commands
probe-mcp init     Create probe.yaml and a sample tasks file
probe-mcp status   Show project overview: config, tasks, results, judge files
probe-mcp eval     Run tasks against an MCP server, save results
probe-mcp judge    Evaluate saved results using an LLM judge
probe-mcp report   Print report from saved results
probe-mcp full     Run eval + judge + report in one command
```

Run any command with `--help` for options:

```bash
probe-mcp eval --help
probe-mcp full --help
```

---

## Getting started

```bash
probe-mcp init
```

Creates `probe.yaml` and `tasks/my_server.yaml` with commented templates. Skips files that already exist.

```bash
probe-mcp status
```

Shows what is in the project: config, task files, results, judge files.

---

## Running the eval

```bash
probe-mcp eval tasks/northwind.yaml
```

Runs all tasks, prints a Rich table of results, saves a JSON results file to `results/`.

```bash
probe-mcp eval tasks/northwind.yaml --verbose
```

Shows full answers and detail lines in addition to the summary table.

```bash
probe-mcp eval tasks/northwind.yaml --compare mcp_server_raw.py --ignore-tool-names
```

Runs the same tasks against two servers and prints a side-by-side comparison table.

---

## Running the judge

```bash
probe-mcp judge results/mcp_server_semantic_2026-05-20_15-38_claude-haiku-4-5_62f7.json
```

Reads a results file, calls a second LLM to evaluate each answer, saves a judge file to `judge/`. The judge evaluates answer quality beyond structural checks, catching cases where the agent gave a technically passing but misleading answer.

```bash
probe-mcp judge results/file.json --model claude-opus-4-5
```

Override the judge model for a single run.

---

## Full pipeline

```bash
probe-mcp full tasks/northwind.yaml
```

Runs eval, then judge, then prints the combined report in one command.

---

## Viewing results

```bash
probe-mcp report results/mcp_server_semantic_2026-05-20_15-38_claude-haiku-4-5_62f7.json
```

Prints the structural results and judge verdicts together. Automatically finds the matching judge file if it exists.

---

## Configuration

`probe.yaml` at the project root controls model selection and output directories:

```yaml
models:
  agent: claude-haiku-4-5   # model used to run tasks
  judge: claude-haiku-4-5   # model used to evaluate results

output:
  results_dir: results
  judge_dir: judge
```

All fields are optional. Defaults are used if `probe.yaml` does not exist.

---

## Writing tasks

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

- `tools_called_includes` — tool names that must appear in the trace
- `max_calls` — maximum number of tool calls allowed
- `answer_includes` — string that must appear in the final answer

---

## File naming

Results and judge files are named to include the server, timestamp, model, and a short random ID:

```
results/mcp_server_semantic_2026-05-20_15-38_claude-haiku-4-5_62f7.json
judge/mcp_server_semantic_2026-05-20_15-38_claude-haiku-4-5_62f7_judge_claude-haiku-4-5_c600.json
```

Every filename reflects exactly what was used. No placeholder model names.

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

- Async parallel execution for compare runs
- Multi-model support: run the same tasks against different LLMs
- More task examples beyond the Northwind baseline
- Pre-built adapters for third-party APIs

---

## Read more

Full write-up with context and analysis: [Your API Works Fine. Your Agent Doesn't.](https://medium.com/@adelkhalil)

---

## License

MIT
