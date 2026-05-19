import asyncio

import click

from probe.loader import load_tasks
from probe.runner import run_suite
from probe.scorer import score_task


@click.command()
@click.argument("tasks_file")
@click.option("--server", default=None, help="Override the server from the task file")
@click.option("--ignore-tool-names", is_flag=True, default=False, help="Skip tool name checks")
def eval(tasks_file: str, server: str, ignore_tool_names: bool):
    """Run an eval suite against an MCP server."""
    suite = load_tasks(tasks_file)

    if server:
        suite["server"] = server

    if ignore_tool_names:
        for task in suite["tasks"]:
            task["expect"].pop("tools_called_includes", None)

    results = asyncio.run(run_suite(suite))

    scored = [score_task(r) for r in results]

    total = len(scored)
    passed = sum(1 for r in scored if r["status"] == "PASS")

    print(f"\nResults: {passed}/{total} passed\n")

    for r in scored:
        icon = "✓" if r["status"] == "PASS" else "✗"
        print(f"  {icon} {r['id']} ({r['call_count']} calls)")
        for msg in r["failed"]:
            if not r['answer'].startswith("ERROR:"):
                print(f"      FAIL: {msg}")
        for msg in r["passed"]:
            print(f"      pass: {msg}")
        answer = r["answer"]
        if answer.startswith("ERROR:"):
            import re

            match = re.search(r"'message': '([^']+)'", answer)
            if match:
                print(f"      error: {match.group(1)[:120]}")
            else:
                print(f"      error: {answer[7:127]}")
        else:
            truncated = answer[:80]
            if len(answer) > 80:
                last_space = truncated.rfind(" ")
                if last_space > 40:
                    truncated = truncated[:last_space]
            print(f"      answer: {truncated}...")
        print()


if __name__ == "__main__":
    eval()
