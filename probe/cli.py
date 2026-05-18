import asyncio

import click

from probe.loader import load_tasks
from probe.runner import run_suite
from probe.scorer import score_task


@click.command()
@click.argument("tasks_file")
@click.option("--server", default=None, help="Override the server from the task file")
def eval(tasks_file: str, server: str):
    """Run an eval suite against an MCP server."""
    suite = load_tasks(tasks_file)

    if server:
        suite["server"] = server

    results = asyncio.run(run_suite(suite))

    scored = [score_task(r) for r in results]

    total = len(scored)
    passed = sum(1 for r in scored if r["status"] == "PASS")

    print(f"\nResults: {passed}/{total} passed\n")

    for r in scored:
        icon = "✓" if r["status"] == "PASS" else "✗"
        print(f"  {icon} {r['id']} ({r['call_count']} calls)")
        for msg in r["failed"]:
            print(f"      FAIL: {msg}")
        for msg in r["passed"]:
            print(f"      pass: {msg}")
        print(f"      answer: {r['answer'][:80]}...")
        print()

if __name__ == "__main__":
        eval()
