import asyncio
import copy
import json
import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import IO

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from probe.config import (
    get_agent_model,
    get_judge_dir,
    get_judge_model,
    get_max_tokens,
    get_results_dir,
    load_config,
)
from probe.judge import judge_results_file
from probe.loader import _find_servers_yaml, _load_servers, load_tasks
from probe.reporter import console, print_compare_table, print_results, print_verdicts
from probe.runner import run_suite
from probe.scorer import score_task


def _working_dir() -> Path:
    """Return the user's actual working directory.

    When probe-mcp is run via the uv alias with --directory, uv changes
    cwd to the package directory. We pass the original cwd via the
    PROBE_CWD environment variable to preserve it.
    """
    probe_cwd = os.environ.get("PROBE_CWD")
    if probe_cwd:
        return Path(probe_cwd)
    return Path.cwd()


_PROBE_YAML = """\
models:
  agent: claude-haiku-4-5
  judge: claude-haiku-4-5
max_tokens: 4096
output:
  results_dir: results
  judge_dir: judge
"""

_SERVERS_YAML = """\
# Define named servers that your task files can reference.
# Each entry sets the command and args used to spawn the MCP server subprocess.
# Paths in args are resolved relative to this file's directory.
#
# Example (uv project in the same directory):
#
# servers:
#   my_server:
#     command: uv
#     args: ["run", "--directory", ".", "python", "my_mcp_server.py"]
servers:
  my_server:
    command: uv
    args: ["run", "--directory", ".", "python", "my_mcp_server.py"]
"""

_SAMPLE_TASKS = """\
# MCP server to test — must match a key in servers.yaml
server: my_server

tasks:
  - id: example_task
    prompt: "Find me all customers from Germany"
    expect:
      deterministic:
        tools_called_includes: [get_customers]
        max_calls: 2
        answer_includes: "Germany"
      probabilistic:
        judge: true
"""


def _run_async(coro):
    try:
        return asyncio.run(coro)
    except (FileNotFoundError, ValueError) as e:
        raise click.ClickException(str(e))


def _load_tasks_or_exit(tasks_file: str, server_override: str | None = None) -> dict:
    try:
        return load_tasks(tasks_file, server_override=server_override)
    except (FileNotFoundError, ValueError) as e:
        raise click.ClickException(str(e))


def _load_json_or_exit(path: str, label: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise click.ClickException(f"{label} not found: {path}")
    except json.JSONDecodeError as e:
        raise click.ClickException(f"{label} is not valid JSON ({path}): {e}")


def _make_log_console(
    log_dir: str | None,
    results_path: str,
    suffix: str = "",
) -> tuple[Console | None, IO | None]:
    """Open a plain-text log file and return (log_console, file_handle).

    Returns (None, None) when log_dir is None (logging disabled).
    log_dir="" means use the same directory as results_path.
    """
    if log_dir is None:
        return None, None

    target_dir = Path(log_dir) if log_dir else Path(results_path).parent
    target_dir.mkdir(parents=True, exist_ok=True)
    log_filename = Path(results_path).stem + suffix + ".log"
    log_path = target_dir / log_filename
    fp = open(log_path, "w", encoding="utf-8")
    lc = Console(file=fp, highlight=False)
    return lc, fp


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
        ("init", "Create probe.yaml, servers.yaml, and a sample tasks file"),
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
    content.append("  2. Edit servers.yaml and tasks/my_server.yaml\n")
    content.append("  3. probe-mcp full tasks/my_server.yaml\n")

    content.append("\nRun any command with --help for options:\n", style="bold")
    content.append("  probe-mcp eval --help\n")

    content.append("\nprobe.yaml config:\n", style="bold")
    content.append("  models:\n")
    content.append("    agent: claude-haiku-4-5\n")
    content.append("    judge: claude-haiku-4-5\n")
    content.append("  max_tokens: 4096\n")
    content.append("  output:\n")
    content.append("    results_dir: results\n")
    content.append("    judge_dir: judge\n")

    console.print(Panel(content, title="[bold]probe-mcp[/bold] — MCP server eval harness", border_style="blue"))


@cli.command()
@click.option("--force", is_flag=True, default=False, help="Overwrite existing files")
def init(force: bool):
    """Create probe.yaml, servers.yaml, and a sample tasks file to get started."""
    (_working_dir() / "tasks").mkdir(exist_ok=True)

    files = [
        ("probe.yaml", _PROBE_YAML),
        ("servers.yaml", _SERVERS_YAML),
        ("tasks/my_server.yaml", _SAMPLE_TASKS),
    ]

    created = 0
    for filepath, content in files:
        p = _working_dir() / filepath
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
        console.print("  1. Edit [cyan]servers.yaml[/cyan] to define your MCP server")
        console.print("  2. Edit [cyan]tasks/my_server.yaml[/cyan] to write your tasks")
        console.print("  3. Run: [cyan]probe-mcp full tasks/my_server.yaml[/cyan]")
    else:
        console.print("[dim]All files already exist. Run: probe-mcp full tasks/my_server.yaml[/dim]")


@cli.command()
def status():
    """Show project overview: config, servers, task files, results, and judge files."""
    config = load_config()

    # Section 1 — Config
    console.rule("[bold]Config[/bold]")
    cfg_table = Table(box=box.ROUNDED, show_header=False)
    cfg_table.add_column("Setting", style="cyan")
    cfg_table.add_column("Value")
    cfg_table.add_row("agent model", get_agent_model(config))
    cfg_table.add_row("judge model", get_judge_model(config))
    cfg_table.add_row("max_tokens", str(get_max_tokens(config)))
    cfg_table.add_row("results_dir", get_results_dir(config))
    cfg_table.add_row("judge_dir", get_judge_dir(config))
    console.print(cfg_table)
    console.print()

    # Section 2 — Servers
    console.rule("[bold]Servers[/bold]")
    try:
        # Use a dummy task path so lookup starts from working dir
        _dummy = _working_dir() / "tasks" / "_dummy.yaml"
        servers_yaml_path = _find_servers_yaml(_dummy)
        servers = _load_servers(servers_yaml_path)
        srv_table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        srv_table.add_column("Name", style="cyan")
        srv_table.add_column("Command")
        srv_table.add_column("Args")
        for name, entry in servers.items():
            srv_table.add_row(name, entry["command"], " ".join(entry["args"]))
        console.print(srv_table)
        console.print(f"[dim]  {servers_yaml_path}[/dim]")
    except FileNotFoundError:
        console.print("[dim]No servers.yaml found. Run: probe-mcp init[/dim]")
    except (ValueError, Exception) as e:
        console.print(f"[red]Error reading servers.yaml: {e}[/red]")
    console.print()

    # Section 3 — Task files
    console.rule("[bold]Task Files[/bold]")
    tasks_path = _working_dir() / "tasks"
    task_files = sorted(tasks_path.glob("*.yaml")) if tasks_path.exists() else []
    if task_files:
        task_table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        task_table.add_column("File", style="cyan")
        task_table.add_column("Tasks", justify="right")
        task_table.add_column("Server")
        for f in task_files:
            try:
                suite = load_tasks(str(f))
                server_display = suite["server"]["name"]
                task_table.add_row(f.name, str(len(suite["tasks"])), server_display)
            except Exception:
                # Try loading the raw YAML just to get task count and server name
                try:
                    import yaml
                    raw = yaml.safe_load(f.read_text())
                    task_count = str(len(raw.get("tasks", []))) if isinstance(raw.get("tasks"), list) else "?"
                    server_name = raw.get("server", "?") if isinstance(raw.get("server"), str) else "?"
                    task_table.add_row(f.name, task_count, f"[yellow]{server_name}[/yellow]")
                except Exception:
                    task_table.add_row(f.name, "?", "[red]error reading file[/red]")
        console.print(task_table)
    else:
        console.print("[dim]No task files found[/dim]")
    console.print()

    # Section 4 — Results
    console.rule("[bold]Results[/bold]")
    results_path = _working_dir() / get_results_dir(config)
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

    # Section 5 — Judge files
    console.rule("[bold]Judge Files[/bold]")
    judge_path = _working_dir() / get_judge_dir(config)
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
@click.option("--server", default=None, help="Override the server (server name from servers.yaml)")
@click.option("--compare", default=None, help="Second server name (from servers.yaml) to run tasks against for comparison")
@click.option("--verbose", is_flag=True, default=False, help="Show MCP server output and full answers")
@click.option(
    "--log", "log_dir", default=None, is_flag=False, flag_value="",
    metavar="[DIR]", help="Write plain-text log to DIR (default: alongside results)",
)
def eval(tasks_file: str, server: str, compare: str, verbose: bool, log_dir: str | None):
    """Run an eval suite against an MCP server."""
    suite = _load_tasks_or_exit(tasks_file, server_override=server)

    # Pre-generate run_id so log filename can match results filename
    pre_run_id = secrets.token_hex(2) if log_dir is not None else None

    if compare:
        suite2 = _load_tasks_or_exit(tasks_file, server_override=compare)

        pre_run_id2 = secrets.token_hex(2) if log_dir is not None else None

        if log_dir is not None:
            _cfg = load_config()
            _ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
            _model = get_agent_model(_cfg)
            _rdir = get_results_dir(_cfg)
            _exp1 = str(Path(_rdir) / f"{suite['server']['name']}_{_ts}_{_model}_{pre_run_id}.json")
            _exp2 = str(Path(_rdir) / f"{suite2['server']['name']}_{_ts}_{_model}_{pre_run_id2}.json")
            lc, fp = _make_log_console(log_dir, _exp1)
            lc2, fp2 = _make_log_console(log_dir, _exp2)
        else:
            lc, fp = None, None
            lc2, fp2 = None, None

        async def _run_both_eval():
            return await asyncio.gather(
                run_suite(suite, tasks_file, verbose=verbose, log_console=lc, run_id=pre_run_id),
                run_suite(suite2, tasks_file, verbose=verbose, log_console=lc2, run_id=pre_run_id2),
            )

        (results, results_file), (results2, results_file2) = _run_async(_run_both_eval())
        scored = [score_task(r) for r in results]
        scored2 = [score_task(r) for r in results2]

        server1_name = suite["server"]["name"]
        server2_name = suite2["server"]["name"]

        try:
            print_compare_table(scored, scored2, server1_name, server2_name, log_console=lc)

            passed = sum(1 for r in scored if r["status"] == "PASS")
            passed2 = sum(1 for r in scored2 if r["status"] == "PASS")
            total = len(scored)
            console.print(f"[bold]{server1_name}[/bold]: {passed}/{total}    [bold]{server2_name}[/bold]: {passed2}/{total}")
            if lc:
                lc.print(f"{server1_name}: {passed}/{total}    {server2_name}: {passed2}/{total}")

            print_results(scored, server1_name, verbose=verbose, log_console=lc)
            console.print(f"[dim]Saved: {results_file}[/dim]")
            if lc:
                lc.print(f"Saved: {results_file}")

            print_results(scored2, server2_name, verbose=verbose, log_console=lc2)
            console.print(f"[dim]Saved: {results_file2}[/dim]")
            if lc2:
                lc2.print(f"Saved: {results_file2}")
        finally:
            if fp:
                fp.close()
            if fp2:
                fp2.close()
    else:
        if log_dir is not None:
            _cfg = load_config()
            _stem = suite["server"]["name"]
            _ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
            _model = get_agent_model(_cfg)
            _rdir = get_results_dir(_cfg)
            _exp = str(Path(_rdir) / f"{_stem}_{_ts}_{_model}_{pre_run_id}.json")
            lc, fp = _make_log_console(log_dir, _exp)
        else:
            lc, fp = None, None
        try:
            results, results_file = _run_async(
                run_suite(suite, tasks_file, verbose=verbose, log_console=lc, run_id=pre_run_id)
            )
            scored = [score_task(r) for r in results]
            print_results(scored, suite["server"]["name"], verbose=verbose, log_console=lc)
            console.print(f"[dim]Saved: {results_file}[/dim]")
            if lc:
                lc.print(f"Saved: {results_file}")
        finally:
            if fp:
                fp.close()


@cli.command()
@click.argument("results_file")
@click.option("--model", default=None, help="Override judge model from config")
@click.option(
    "--log", "log_dir", default=None, is_flag=False, flag_value="",
    metavar="[DIR]", help="Write plain-text log to DIR (default: alongside results)",
)
def judge(results_file: str, model: str, log_dir: str | None):
    """Run the LLM judge on a results file."""
    config = load_config()
    judge_model = model or get_judge_model(config)
    judge_dir = get_judge_dir(config)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    lc, fp = _make_log_console(log_dir, results_file, suffix=f"_judge_{timestamp}")
    try:
        output_file = _run_async(
            judge_results_file(results_file, judge_model, judge_dir, log_console=lc)
        )

        with open(output_file) as f:
            data = json.load(f)

        print_verdicts(data["verdicts"], judge_model, log_console=lc)
        console.print(f"[dim]Saved: {output_file}[/dim]")
        if lc:
            lc.print(f"Saved: {output_file}")
    finally:
        if fp:
            fp.close()


@cli.command()
@click.argument("results_file")
@click.option("--verbose", is_flag=True, default=False, help="Show full answers and detail lines")
@click.option(
    "--log", "log_dir", default=None, is_flag=False, flag_value="",
    metavar="[DIR]", help="Write plain-text log to DIR (default: alongside results)",
)
def report(results_file: str, verbose: bool, log_dir: str | None):
    """Print a combined report for a results file, including judge verdicts if available."""
    config = load_config()
    judge_dir = get_judge_dir(config)

    data = _load_json_or_exit(results_file, "Results file")

    meta = data.get("meta", {})
    results = data.get("results", [])
    scored = [score_task(r) for r in results]

    judge_path = Path(judge_dir)
    results_stem = Path(results_file).stem
    judge_files = list(judge_path.glob(f"{results_stem}_judge_*.json")) if judge_path.exists() else []

    verdicts_by_id = None
    judge_data = None
    if judge_files:
        latest = max(judge_files, key=lambda p: p.stat().st_mtime)
        judge_data = _load_json_or_exit(str(latest), "Judge file")
        verdicts_by_id = {v["id"]: v["verdict"] for v in judge_data["verdicts"]}

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    lc, fp = _make_log_console(log_dir, results_file, suffix=f"_report_{timestamp}")
    try:
        print_results(scored, meta.get("server", "unknown"), verbose=verbose, verdicts=verdicts_by_id, log_console=lc)

        if judge_data:
            print_verdicts(judge_data["verdicts"], judge_data["meta"].get("judge_model", "unknown"), log_console=lc)
        else:
            msg = "[dim](No judge file found. Run `probe-mcp judge` to add LLM verdicts.)[/dim]"
            console.print(msg)
            if lc:
                lc.print("(No judge file found. Run `probe-mcp judge` to add LLM verdicts.)")
    finally:
        if fp:
            fp.close()


@cli.command()
@click.argument("tasks_file")
@click.option("--server", default=None, help="Override the server (server name from servers.yaml)")
@click.option("--compare", default=None, help="Second server name (from servers.yaml) to run tasks against for comparison")
@click.option("--judge-model", default=None, help="Override judge model from config")
@click.option("--verbose", is_flag=True, default=False, help="Show MCP server output and full answers")
@click.option(
    "--log", "log_dir", default=None, is_flag=False, flag_value="",
    metavar="[DIR]", help="Write plain-text log to DIR (default: alongside results)",
)
def full(tasks_file: str, server: str, compare: str, judge_model: str, verbose: bool, log_dir: str | None):
    """Run eval, then judge, then report in sequence."""
    config = load_config()
    suite = _load_tasks_or_exit(tasks_file, server_override=server)

    pre_run_id = secrets.token_hex(2) if log_dir is not None else None

    results2_file = None
    if compare:
        suite2 = _load_tasks_or_exit(tasks_file, server_override=compare)

        pre_run_id2 = secrets.token_hex(2) if log_dir is not None else None

        if log_dir is not None:
            _ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
            _model = get_agent_model(config)
            _rdir = get_results_dir(config)
            _exp1 = str(Path(_rdir) / f"{suite['server']['name']}_{_ts}_{_model}_{pre_run_id}.json")
            _exp2 = str(Path(_rdir) / f"{suite2['server']['name']}_{_ts}_{_model}_{pre_run_id2}.json")
            lc, fp = _make_log_console(log_dir, _exp1)
            lc2, fp2 = _make_log_console(log_dir, _exp2)
        else:
            lc, fp = None, None
            lc2, fp2 = None, None

        async def _run_both_full():
            return await asyncio.gather(
                run_suite(suite, tasks_file, verbose=verbose, log_console=lc, run_id=pre_run_id),
                run_suite(suite2, tasks_file, verbose=verbose, log_console=lc2, run_id=pre_run_id2),
            )

        (results, results_file), (results2, results2_file) = _run_async(_run_both_full())
        scored = [score_task(r) for r in results]
        scored2 = [score_task(r) for r in results2]
    else:
        if log_dir is not None:
            _stem = suite["server"]["name"]
            _ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
            _model = get_agent_model(config)
            _rdir = get_results_dir(config)
            _exp = str(Path(_rdir) / f"{_stem}_{_ts}_{_model}_{pre_run_id}.json")
            lc, fp = _make_log_console(log_dir, _exp)
        else:
            lc, fp = None, None
        lc2, fp2 = None, None
        results, results_file = _run_async(
            run_suite(suite, tasks_file, verbose=verbose, log_console=lc, run_id=pre_run_id)
        )
        scored = [score_task(r) for r in results]

    server1_name = suite["server"]["name"]

    try:
        if compare and results2_file:
            server2_name = suite2["server"]["name"]
            print_compare_table(scored, scored2, server1_name, server2_name, log_console=lc)

            passed = sum(1 for r in scored if r["status"] == "PASS")
            passed2 = sum(1 for r in scored2 if r["status"] == "PASS")
            total = len(scored)
            console.print(f"[bold]{server1_name}[/bold]: {passed}/{total}    [bold]{server2_name}[/bold]: {passed2}/{total}")
            if lc:
                lc.print(f"{server1_name}: {passed}/{total}    {server2_name}: {passed2}/{total}")
            console.print(f"[dim]Saved: {results_file}[/dim]")
            if lc:
                lc.print(f"Saved: {results_file}")
            console.print(f"[dim]Saved: {results2_file}[/dim]")
            if lc2:
                lc2.print(f"Saved: {results2_file}")

        j_model = judge_model or get_judge_model(config)
        judge_dir = get_judge_dir(config)

        judge_file = _run_async(judge_results_file(results_file, j_model, judge_dir, log_console=lc))
        with open(judge_file) as f:
            judge_data = json.load(f)
        verdicts_by_id = {v["id"]: v["verdict"] for v in judge_data["verdicts"]}

        print_results(scored, server1_name, verbose=verbose, verdicts=verdicts_by_id, log_console=lc)
        print_verdicts(judge_data["verdicts"], j_model, log_console=lc)
        console.print(f"[dim]Saved: {judge_file}[/dim]")
        if lc:
            lc.print(f"Saved: {judge_file}")

        if compare and results2_file:
            judge_file2 = _run_async(judge_results_file(results2_file, j_model, judge_dir, log_console=lc2))
            with open(judge_file2) as f:
                judge_data2 = json.load(f)
            verdicts2_by_id = {v["id"]: v["verdict"] for v in judge_data2["verdicts"]}

            print_results(scored2, server2_name, verbose=verbose, verdicts=verdicts2_by_id, log_console=lc2)
            print_verdicts(judge_data2["verdicts"], j_model, log_console=lc2)
            console.print(f"[dim]Saved: {judge_file2}[/dim]")
            if lc2:
                lc2.print(f"Saved: {judge_file2}")
    finally:
        if fp:
            fp.close()
        if fp2:
            fp2.close()


if __name__ == "__main__":
    cli()
