import asyncio
import sys

from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

client = Anthropic()

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


async def run_task(task: dict, session: ClientSession, tools: list) -> dict:
    """Run a single task against MCP server and return the trace."""
    messages = [{
        "role": "user",
        "content": task["prompt"],
    }]
    trace = []

    while True:
        try:
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1000,
                tools=tools,
                messages=messages,
            )
        except Exception as e:
            return {
                "trace": trace,
                "answer": f"ERROR: {str(e)[:200]}",
                "error": True,
            }

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason != "tool_use":
            break

        tool_calls = [
            block for block in response.content
            if block.type == "tool_use"
        ]

        messages.append({
            "role": "assistant",
            "content": response.content,
        })

        tool_results = []
        for tool_call in tool_calls:
            result = await session.call_tool(
                tool_call.name,
                tool_call.input,
            )
            trace.append({
                "tool": tool_call.name,
                "params": tool_call.input,
            })
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_call.id,
                "content": str(result.content),
            })

        messages.append({
            "role": "user",
            "content": tool_results,
        })

    final_answer = next(
        (block.text for block in response.content if hasattr(block, "text")),
        ""
    )

    return {"trace": trace, "answer": final_answer}

async def run_suite(suite: dict) -> list:
    """Run all tasks in a suite against the MCP server."""
    server_path = suite["server"]

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_path],
    )

    results = []

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await get_tools(session)

            for task in suite["tasks"]:
                print(f"Running: {task['id']}")
                result = await run_task(task, session, tools)
                results.append({
                    "id": task["id"],
                    "trace": result["trace"],
                    "answer": result["answer"],
                    "expect": task["expect"],
                })

    return results
