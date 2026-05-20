import asyncio
import copy
import json
from pathlib import Path

import click
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from probe.config import get_agent_model, get_judge_dir, get_judge_model, get_results_dir, load_config
from probe.judge import judge_results_file
from probe.loader import load_tasks
from probe.reporter import console, print_compare_table, print_results, print_summary, print_verdicts
from probe.runner import run_suite
from probe.scorer import score_task

_PROBE_YAML = """\
models:
  agent: claude-haiku-4-5
  judge: claude-haiku-4-5
output:
  results_dir: results
  judge_dir: judge
"""

_SAMPLE_TASKS = """\
# MCP server to test
server: my_mcp_server.py

tasks:
  - id: example_task
    prompt: "Find me all customers from Germany"
    expect:
      tools_called_includes: [get_customers]
      max_calls: 2
      answer_includes: "Germany"
"""


@click.group()
def cli():
    """probe-mcp: eval harness for MCP servers."""
    pass


@cli.command(name="help")
def help_command():
    """Show workflow guide and available commands."""
    content = Text()

    content.append("Commands:\n", style="bold")
    commands = [
        ("init", "Create probe.yaml and a sample tasks file"),
        ("eval", "Run tasks against an MCP server, save results to results/"),
        ("judge", "Evaluate saved results with an LLM judge, save to judge/"),
        ("report", "Print report from saved results"),
        ("full", "Run eval + judge + report in one command"),
    ]
    for cmd, desc in commands:
        content.append(f"  {cmd:<8}", style="cyan bold")
        content.append(f"{desc}\n")

    content.append("\nTypical workflow:\n", style="bold")
    content.append("  1. probe-mcp init\n")
    content.append("  2. Edit tasks/my_server.yaml\n")
    content.append("  3. probe-mcp full tasks/my_server.yaml\n")

    content.append("\nRun any command with --help for options:\n", style="bold")
    content.append("  probe-mcp eval --help\n")

    content.append("\nprobe.yaml config:\n", style="bold")
    content.append("  models:\n")
    content.append("    agent: claude-haiku-4-5\n")
    content.append("    judge: claude-haiku-4-5\n")
    content.append("  output:\n")
    content.append("    results_dir: results\n")
    content.append("    judge_dir: judge\n")

    console.print(Panel(content, title="[bold]probe-mcp[/bold] — MCP server eval harness", border_style="blue"))


@cli.command()
@click.option("--force", is_flag=True, default=False, help="Overwrite existing files")
def init(force: bool):
    """Create probe.yaml and a sample tasks file to get started."""
    Path("tasks").mkdir(exist_ok=True)

    files = [
        ("probe.yaml", _PROBE_YAML),
        ("tasks/my_server.yaml", _SAMPLE_TASKS),
    ]

    created = 0
    for filepath, content in files:
        p = Path(filepath)
        if not p.exists():
            p.write_text(content)
            console.print(f"[green]Created {filepath}[/green]")
            created += 1
        elif force:
            p.write_text(content)
            console.print(f"[yellow]Overwriting {filepath}[/yellow]")
            created += 1
        else:
            console.print(f"[dim]{filepath} already exists, skipping.[/dim]")

    console.print()
    if created > 0:
        console.print("[bold]Next steps:[/bold]")
        console.print("  1. Edit [cyan]tasks/my_server.yaml[/cyan] to match your MCP server")
        console.print("  2. Run: [cyan]probe-mcp full tasks/my_server.yaml[/cyan]")
    else:
        console.print("[dim]All files already exist. Run: probe-mcp full tasks/my_server.yaml[/dim]")


@cli.command()
def status():
    """Show project overview: config, task files, results, and judge files."""
    config = load_config()

    # Section 1 — Config
    console.rule("[bold]Config[/bold]")
    cfg_table = Table(box=box.ROUNDED, show_header=False)
    cfg_table.add_column("Setting", style="cyan")
    cfg_table.add_column("Value")
    cfg_table.add_row("agent model", get_agent_model(config))
    cfg_table.add_row("judge model", get_judge_model(config))
    cfg_table.add_row("results_dir", get_results_dir(config))
    cfg_table.add_row("judge_dir", get_judge_dir(config))
    console.print(cfg_table)
    console.print()

    # Section 2 — Task files
    console.rule("[bold]Task Files[/bold]")
    tasks_path = Path("tasks")
    task_files = sorted(tasks_path.glob("*.yaml")) if tasks_path.exists() else []
    if task_files:
        task_table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        task_table.add_column("File", style="cyan")
        task_table.add_column("Tasks", justify="right")
        task_table.add_column("Server")
        for f in task_files:
            try:
                suite = load_tasks(str(f))
                task_table.add_row(f.name, str(len(suite["tasks"])), suite["server"])
            except Exception:
                task_table.add_row(f.name, "?", "[red]error reading file[/red]")
        console.print(task_table)
    else:
        console.print("[dim]No task files found[/dim]")
    console.print()

    # Section 3 — Results
    console.rule("[bold]Results[/bold]")
    results_path = Path(get_results_dir(config))
    result_files = (
        sorted(results_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if results_path.exists()
        else []
    )
    if result_files:
        res_table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        res_table.add_column("File", style="cyan")
        res_table.add_column("Score", justify="right")
        for f in result_files:
            try:
                data = json.loads(f.read_text())
                scored = [score_task(r) for r in data.get("results", [])]
                passed = sum(1 for r in scored if r["status"] == "PASS")
                res_table.add_row(f.name, f"{passed}/{len(scored)}")
            except Exception:
                res_table.add_row(f.name, "?")
        console.print(res_table)
    else:
        console.print("[dim]No results yet. Run: probe-mcp eval[/dim]")
    console.print()

    # Section 4 — Judge files
    console.rule("[bold]Judge Files[/bold]")
    judge_path = Path(get_judge_dir(config))
    judge_files = (
        sorted(judge_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if judge_path.exists()
        else []
    )
    if judge_files:
        jdg_table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        jdg_table.add_column("File", style="cyan")
        jdg_table.add_column("Verdicts", justify="right")
        for f in judge_files:
            try:
                data = json.loads(f.read_text())
                jdg_table.add_row(f.name, str(len(data.get("verdicts", []))))
            except Exception:
                jdg_table.add_row(f.name, "?")
        console.print(jdg_table)
    else:
        console.print("[dim]No judge files yet. Run: probe-mcp judge[/dim]")
    console.print()


@cli.command()
@click.argument("tasks_file")
@click.option("--server", default=None, help="Override the server from the task file")
@click.option("--ignore-tool-names", is_flag=True, default=False, help="Skip tool name checks")
@click.option("--compare", default=None, help="Second server to run tasks against for comparison")
@click.option("--verbose", is_flag=True, default=False, help="Show MCP server output and full answers")
def eval(tasks_file: str, server: str, ignore_tool_names: bool, compare: str, verbose: bool):
    """Run an eval suite against an MCP server."""
    suite = load_tasks(tasks_file)

    if server:
        suite["server"] = server

    if ignore_tool_names:
        for task in suite["tasks"]:
            task["expect"].pop("tools_called_includes", None)

    results, results_file = asyncio.run(run_suite(suite, tasks_file, verbose=verbose))
    scored = [score_task(r) for r in results]

    print_results(scored, suite["server"], verbose=verbose)
    console.print(f"[dim]Saved: {results_file}[/dim]")

    if compare:
        suite2 = copy.deepcopy(suite)
        suite2["server"] = compare
        if ignore_tool_names:
            for task in suite2["tasks"]:
                task["expect"].pop("tools_called_includes", None)

        results2, results_file2 = asyncio.run(run_suite(suite2, tasks_file, verbose=verbose))
        scored2 = [score_task(r) for r in results2]

        print_compare_table(scored, scored2, suite["server"], compare)

        passed = sum(1 for r in scored if r["status"] == "PASS")
        passed2 = sum(1 for r in scored2 if r["status"] == "PASS")
        total = len(scored)
        console.print(f"[bold]{suite['server']}[/bold]: {passed}/{total}    [bold]{compare}[/bold]: {passed2}/{total}")

        print_results(scored2, compare, verbose=verbose)
        console.print(f"[dim]Saved: {results_file2}[/dim]")


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

    print_verdicts(data["verdicts"], judge_model)
    console.print(f"[dim]Saved: {output_file}[/dim]")


@cli.command()
@click.argument("results_file")
@click.option("--verbose", is_flag=True, default=False, help="Show full answers and detail lines")
def report(results_file: str, verbose: bool):
    """Print a combined report for a results file, including judge verdicts if available."""
    config = load_config()
    judge_dir = get_judge_dir(config)

    with open(results_file) as f:
        data = json.load(f)

    meta = data.get("meta", {})
    results = data.get("results", [])
    scored = [score_task(r) for r in results]

    print_results(scored, meta.get("server", "unknown"), verbose=verbose)

    judge_path = Path(judge_dir)
    results_stem = Path(results_file).stem
    judge_files = list(judge_path.glob(f"{results_stem}_judge_*.json")) if judge_path.exists() else []

    if judge_files:
        latest = max(judge_files, key=lambda p: p.stat().st_mtime)
        with open(latest) as f:
            judge_data = json.load(f)
        print_verdicts(judge_data["verdicts"], judge_data["meta"].get("judge_model", "unknown"))
    else:
        console.print("[dim](No judge file found. Run `probe-mcp judge` to add LLM verdicts.)[/dim]")


@cli.command()
@click.argument("tasks_file")
@click.option("--server", default=None, help="Override the server from the task file")
@click.option("--ignore-tool-names", is_flag=True, default=False, help="Skip tool name checks")
@click.option("--compare", default=None, help="Second server to run tasks against for comparison")
@click.option("--judge-model", default=None, help="Override judge model from config")
@click.option("--verbose", is_flag=True, default=False, help="Show MCP server output and full answers")
def full(tasks_file: str, server: str, ignore_tool_names: bool, compare: str, judge_model: str, verbose: bool):
    """Run eval, then judge, then report in sequence."""
    config = load_config()
    suite = load_tasks(tasks_file)

    if server:
        suite["server"] = server

    if ignore_tool_names:
        for task in suite["tasks"]:
            task["expect"].pop("tools_called_includes", None)

    results, results_file = asyncio.run(run_suite(suite, tasks_file, verbose=verbose))
    scored = [score_task(r) for r in results]

    print_results(scored, suite["server"], verbose=verbose)
    console.print(f"[dim]Saved: {results_file}[/dim]")

    results2_file = None
    scored2 = None
    if compare:
        suite2 = copy.deepcopy(suite)
        suite2["server"] = compare
        if ignore_tool_names:
            for task in suite2["tasks"]:
                task["expect"].pop("tools_called_includes", None)

        results2, results2_file = asyncio.run(run_suite(suite2, tasks_file, verbose=verbose))
        scored2 = [score_task(r) for r in results2]

        print_compare_table(scored, scored2, suite["server"], compare)

        passed = sum(1 for r in scored if r["status"] == "PASS")
        passed2 = sum(1 for r in scored2 if r["status"] == "PASS")
        total = len(scored)
        console.print(f"[bold]{suite['server']}[/bold]: {passed}/{total}    [bold]{compare}[/bold]: {passed2}/{total}")

        print_results(scored2, compare, verbose=verbose)
        console.print(f"[dim]Saved: {results2_file}[/dim]")

    j_model = judge_model or get_judge_model(config)
    judge_dir = get_judge_dir(config)

    judge_file = asyncio.run(judge_results_file(results_file, j_model, judge_dir))
    with open(judge_file) as f:
        judge_data = json.load(f)

    print_verdicts(judge_data["verdicts"], j_model)
    console.print(f"[dim]Saved: {judge_file}[/dim]")

    if compare and results2_file:
        judge_file2 = asyncio.run(judge_results_file(results2_file, j_model, judge_dir))
        with open(judge_file2) as f:
            judge_data2 = json.load(f)

        print_verdicts(judge_data2["verdicts"], j_model)
        console.print(f"[dim]Saved: {judge_file2}[/dim]")


if __name__ == "__main__":
    cli()
