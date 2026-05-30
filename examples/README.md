# Examples

This folder contains testbeds that demonstrate probe-mcp against real API schemas.
Each example is a self-contained project with its own servers, tasks, and configuration.

---

## Northwind

A classic commerce database used as a reference testbed. Ships two MCP servers
built on the same underlying API:

- `mcp_server_raw.py` — naive 1:1 wrap, representative of auto-generated wrappers
- `mcp_server_semantic.py` — semantic layer with rich descriptions, workflow guidance,
  and shaped responses

Running the eval against both shows the difference tool definition quality makes
on real agent tasks.

```bash
cd northwind
uv sync
cd ../..
uv run python -m probe.cli eval examples/northwind/tasks/northwind.yaml
```

To compare both servers:

```bash
uv run python -m probe.cli eval examples/northwind/tasks/northwind.yaml --compare raw
```

---

## Adding your own example

Each example folder should contain:

```
my_example/
  servers.yaml        # named server definitions
  probe.yaml          # model and output config
  tasks/
    my_tasks.yaml     # eval task suite
  README.md           # what the example demonstrates
  pyproject.toml      # dependencies for the MCP servers
```

See `northwind/` as a reference.
