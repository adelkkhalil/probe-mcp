import asyncio
import json
import os
import secrets
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console

from probe.config import get_agent_model, get_max_tokens, get_results_dir, load_config

_console = Console()

config = load_config()
client = Anthropic()

MAX_ITERATIONS = 20


async def get_tools(session: ClientSession) -> list:
    """Fetch the tool list from the MCP server and convert into Anthropic format"""
    tools_result = await session.list_tools()
    tools = []
    for tool in tools_result.tools:
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema,
        })
    return tools


def _first_text(content) -> str | None:
    return next((block.text for block in content if hasattr(block, "text")), None)


async def run_task(task: dict, session: ClientSession, tools: list) -> dict:
    """Run a single task against MCP server and return the trace."""
    messages = [{"role": "user", "content": task["prompt"]}]
    trace = []
    response = None

    for _ in range(MAX_ITERATIONS):
        try:
            response = client.messages.create(
                model=get_agent_model(config),
                max_tokens=get_max_tokens(config),
                tools=tools,
                messages=messages,
            )
        except Exception as e:
            return {
                "trace": trace,
                "answer": f"ERROR: {str(e)[:200]}",
            }

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason != "tool_use":
            partial = _first_text(response.content) or ""
            return {
                "trace": trace,
                "answer": (
                    f"ERROR: agent stopped early (stop_reason={response.stop_reason}): {partial}"
                )[:300],
            }

        tool_calls = [block for block in response.content if block.type == "tool_use"]
        if not tool_calls:
            return {
                "trace": trace,
                "answer": "ERROR: response had stop_reason=tool_use but contained no tool_use blocks",
            }

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tool_call in tool_calls:
            result = await session.call_tool(tool_call.name, tool_call.input)
            trace.append({"tool": tool_call.name, "params": tool_call.input, "error": result.isError})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_call.id,
                "content": str(result.content),
            })

        messages.append({"role": "user", "content": tool_results})
    else:
        return {
            "trace": trace,
            "answer": f"ERROR: agent exceeded max iterations ({MAX_ITERATIONS})",
        }

    final_answer = _first_text(response.content)
    if final_answer is None:
        return {
            "trace": trace,
            "answer": (
                f"ERROR: agent ended without producing a text response "
                f"(stop_reason={response.stop_reason})"
            ),
        }

    return {"trace": trace, "answer": final_answer}


async def run_suite(
    suite: dict,
    tasks_file: str = "",
    verbose: bool = False,
    log_console: Console | None = None,
    run_id: str | None = None,
) -> tuple[list, str]:
    """Run all tasks in a suite against the MCP server."""
    server_config = suite["server"]

    env = dict(os.environ)
    env.pop("VIRTUAL_ENV", None)  # prevent uv warning when server uses its own venv
    if not verbose:
        env["FASTMCP_SHOW_SERVER_BANNER"] = "false"
        env["FASTMCP_LOG_LEVEL"] = "WARNING"

    server_params = StdioServerParameters(
        command=server_config["command"],
        args=server_config["args"],
        env=env,
        cwd=server_config["cwd"],
    )

    results = []

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # MCP ≤2025-11-25 requires explicit handshake; 2026-07-28+ SDK removes it
            if hasattr(session, "initialize"):
                await session.initialize()
            tools = await get_tools(session)

            for task in suite["tasks"]:
                trials_count = task.get("trials", 1)
                _console.print(f"Running: {task['id']}")
                if log_console:
                    log_console.print(f"Running: {task['id']}")
                if trials_count > 1:
                    trial_results = []
                    for _ in range(trials_count):
                        r = await run_task(task, session, tools)
                        trial_results.append({"trace": r["trace"], "answer": r["answer"]})
                    results.append({
                        "id": task["id"],
                        "prompt": task["prompt"],
                        "trace": trial_results[0]["trace"],
                        "answer": trial_results[0]["answer"],
                        "expect": task["expect"],
                        "trials": trial_results,
                    })
                else:
                    result = await run_task(task, session, tools)
                    results.append({
                        "id": task["id"],
                        "prompt": task["prompt"],
                        "trace": result["trace"],
                        "answer": result["answer"],
                        "expect": task["expect"],
                    })

    agent_model = get_agent_model(config)
    results_dir = get_results_dir(config)
    Path(results_dir).mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    server_stem = server_config["name"]
    timestamp = now.strftime("%Y-%m-%d_%H-%M")
    run_id = run_id or secrets.token_hex(2)
    filename = f"{server_stem}_{timestamp}_{agent_model}_{run_id}.json"
    filepath = Path(results_dir) / filename

    meta = {
        "server": server_config["name"],
        "tasks_file": tasks_file,
        "agent_model": agent_model,
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "run_id": run_id,
    }

    filepath.write_text(json.dumps({"meta": meta, "results": results}, indent=2))
    return results, str(filepath)
