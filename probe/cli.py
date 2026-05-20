import asyncio
import copy
import json
from pathlib import Path

import click

from probe.config import get_judge_dir, get_judge_model, get_results_dir, load_config
from probe.judge import judge_results_file
from probe.loader import load_tasks
from probe.reporter import print_compare_table, print_results, print_summary
from probe.runner import run_suite
from probe.scorer import score_task


@click.group()
def cli():
    """probe-mcp: eval harness for MCP servers."""
    pass


@cli.command()
@click.argument("tasks_file")
@click.option("--server", default=None, help="Override the server from the task file")
@click.option("--ignore-tool-names", is_flag=True, default=False, help="Skip tool name checks")
@click.option("--compare", default=None, help="Second server to run tasks against for comparison")
def eval(tasks_file: str, server: str, ignore_tool_names: bool, compare: str):
    """Run an eval suite against an MCP server."""
    config = load_config()
    suite = load_tasks(tasks_file)

    if server:
        suite["server"] = server

    if ignore_tool_names:
        for task in suite["tasks"]:
            task["expect"].pop("tools_called_includes", None)

    results, results_file = asyncio.run(run_suite(suite, tasks_file))
    scored = [score_task(r) for r in results]

    print_results(scored, suite["server"])
    print(f"Saved: {results_file}")

    if compare:
        suite2 = copy.deepcopy(suite)
        suite2["server"] = compare
        if ignore_tool_names:
            for task in suite2["tasks"]:
                task["expect"].pop("tools_called_includes", None)

        results2, results_file2 = asyncio.run(run_suite(suite2, tasks_file))
        scored2 = [score_task(r) for r in results2]

        print_compare_table(scored, scored2, suite["server"], compare)

        passed = sum(1 for r in scored if r["status"] == "PASS")
        passed2 = sum(1 for r in scored2 if r["status"] == "PASS")
        total = len(scored)
        print(f"\n{suite['server']}: {passed}/{total}    {compare}: {passed2}/{total}")

        print_results(scored2, compare)
        print(f"Saved: {results_file2}")


@cli.command()
@click.argument("results_file")
@click.option("--model", default=None, help="Override judge model from config")
def judge(results_file: str, model: str):
    """Run the LLM judge on a results file."""
    config = load_config()
    judge_model = model or get_judge_model(config)
    judge_dir = get_judge_dir(config)

    output_file = asyncio.run(judge_results_file(results_file, judge_model, judge_dir))

    with open(output_file) as f:
        data = json.load(f)

    print(f"\nJudge results ({judge_model}):\n")
    for v in data["verdicts"]:
        icon = "✓" if v["verdict"] == "PASS" else "~" if v["verdict"] == "PARTIAL" else "✗"
        print(f"  {icon} {v['id']}: {v['verdict']}")
        print(f"      {v['reason']}")

    print(f"\nSaved: {output_file}")


@cli.command()
@click.argument("results_file")
def report(results_file: str):
    """Print a combined report for a results file, including judge verdicts if available."""
    config = load_config()
    judge_dir = get_judge_dir(config)

    with open(results_file) as f:
        data = json.load(f)

    meta = data.get("meta", {})
    results = data.get("results", [])
    scored = [score_task(r) for r in results]

    print_results(scored, meta.get("server", "unknown"))

    judge_path = Path(judge_dir)
    results_stem = Path(results_file).stem
    judge_files = list(judge_path.glob(f"{results_stem}_judge_*.json")) if judge_path.exists() else []

    if judge_files:
        latest = max(judge_files, key=lambda p: p.stat().st_mtime)
        with open(latest) as f:
            judge_data = json.load(f)
        jm = judge_data["meta"].get("judge_model", "unknown")
        print(f"\nJudge verdicts ({jm}):\n")
        for v in judge_data["verdicts"]:
            icon = "✓" if v["verdict"] == "PASS" else "~" if v["verdict"] == "PARTIAL" else "✗"
            print(f"  {icon} {v['id']}: {v['verdict']}")
            print(f"      {v['reason']}")
    else:
        print("\n(No judge file found. Run `probe-mcp judge` to add LLM verdicts.)")


@cli.command()
@click.argument("tasks_file")
@click.option("--server", default=None, help="Override the server from the task file")
@click.option("--ignore-tool-names", is_flag=True, default=False, help="Skip tool name checks")
@click.option("--compare", default=None, help="Second server to run tasks against for comparison")
@click.option("--judge-model", default=None, help="Override judge model from config")
def full(tasks_file: str, server: str, ignore_tool_names: bool, compare: str, judge_model: str):
    """Run eval, then judge, then report in sequence."""
    config = load_config()
    suite = load_tasks(tasks_file)

    if server:
        suite["server"] = server

    if ignore_tool_names:
        for task in suite["tasks"]:
            task["expect"].pop("tools_called_includes", None)

    results, results_file = asyncio.run(run_suite(suite, tasks_file))
    scored = [score_task(r) for r in results]

    print_results(scored, suite["server"])
    print(f"Saved: {results_file}")

    results2_file = None
    scored2 = None
    if compare:
        suite2 = copy.deepcopy(suite)
        suite2["server"] = compare
        if ignore_tool_names:
            for task in suite2["tasks"]:
                task["expect"].pop("tools_called_includes", None)

        results2, results2_file = asyncio.run(run_suite(suite2, tasks_file))
        scored2 = [score_task(r) for r in results2]

        print_compare_table(scored, scored2, suite["server"], compare)

        passed = sum(1 for r in scored if r["status"] == "PASS")
        passed2 = sum(1 for r in scored2 if r["status"] == "PASS")
        total = len(scored)
        print(f"\n{suite['server']}: {passed}/{total}    {compare}: {passed2}/{total}")

        print_results(scored2, compare)
        print(f"Saved: {results2_file}")

    j_model = judge_model or get_judge_model(config)
    judge_dir = get_judge_dir(config)

    judge_file = asyncio.run(judge_results_file(results_file, j_model, judge_dir))
    with open(judge_file) as f:
        judge_data = json.load(f)

    print(f"\nJudge verdicts ({j_model}):\n")
    for v in judge_data["verdicts"]:
        icon = "✓" if v["verdict"] == "PASS" else "~" if v["verdict"] == "PARTIAL" else "✗"
        print(f"  {icon} {v['id']}: {v['verdict']}")
        print(f"      {v['reason']}")
    print(f"\nSaved: {judge_file}")

    if compare and results2_file:
        judge_file2 = asyncio.run(judge_results_file(results2_file, j_model, judge_dir))
        with open(judge_file2) as f:
            judge_data2 = json.load(f)

        print(f"\nJudge verdicts for {compare} ({j_model}):\n")
        for v in judge_data2["verdicts"]:
            icon = "✓" if v["verdict"] == "PASS" else "~" if v["verdict"] == "PARTIAL" else "✗"
            print(f"  {icon} {v['id']}: {v['verdict']}")
            print(f"      {v['reason']}")
        print(f"\nSaved: {judge_file2}")


if __name__ == "__main__":
    cli()
