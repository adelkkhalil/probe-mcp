import asyncio

import click

from probe.loader import load_tasks
from probe.runner import run_suite
from probe.scorer import score_task


@click.command()
@click.argument("tasks_file")
@click.option("--server", default=None, help="Override the server from the task file")
@click.option("--ignore-tool-names", is_flag=True, default=False, help="Skip tool name checks")
@click.option("--compare", default=None, help="Second server to run tasks against for comparison")
def eval(tasks_file: str, server: str, ignore_tool_names: bool, compare: str):
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

    if compare:
        import copy

        suite2 = copy.deepcopy(suite)
        suite2["server"] = compare
        if ignore_tool_names:
            for task in suite2["tasks"]:
                task["expect"].pop("tools_called_includes", None)
        results2 = asyncio.run(run_suite(suite2))
        scored2 = [score_task(r) for r in results2]
        scored2_by_id = {r["id"]: r for r in scored2}

        server1_name = suite["server"]
        server2_name = compare
        col1 = max(len(server1_name), 20)
        col2 = max(len(server2_name), 20)
        task_col = max(len(t["id"]) for t in suite["tasks"]) + 2

        print(f"\n{'Task':<{task_col}}  {server1_name:<{col1}}  {server2_name:<{col2}}")
        print("-" * (task_col + col1 + col2 + 4))

        for r1 in scored:
            r2 = scored2_by_id.get(r1["id"])
            s1 = f"PASS ({r1['call_count']} calls)" if r1["status"] == "PASS" else "FAIL"
            s2 = f"PASS ({r2['call_count']} calls)" if r2 and r2["status"] == "PASS" else "FAIL"
            print(f"{r1['id']:<{task_col}}  {s1:<{col1}}  {s2:<{col2}}")

        passed2 = sum(1 for r in scored2 if r["status"] == "PASS")
        print(f"\n{server1_name}: {passed}/{total}    {server2_name}: {passed2}/{total}")


if __name__ == "__main__":
    eval()
