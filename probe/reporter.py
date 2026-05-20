import re

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()


def _status_cell(status: str) -> Text:
    mapping = {
        "PASS": ("✓ PASS", "bold green"),
        "FAIL": ("✗ FAIL", "bold red"),
        "PARTIAL": ("~ PARTIAL", "bold blue"),
        "WARN": ("! WARN", "bold yellow"),
        "ERROR": ("! ERROR", "bold yellow"),
    }
    label, style = mapping.get(status, (status, "white"))
    return Text(label, style=style)


def _verdict_cell(verdict: str) -> Text:
    mapping = {
        "PASS": ("✓ PASS", "bold green"),
        "PARTIAL": ("~ PARTIAL", "bold blue"),
        "FAIL": ("✗ FAIL", "bold red"),
        "ERROR": ("! ERROR", "bold yellow"),
    }
    label, style = mapping.get(verdict, (verdict, "white"))
    return Text(label, style=style)


def print_results(scored: list, server_name: str, verbose: bool = False):
    total = len(scored)
    passed = sum(1 for r in scored if r["status"] == "PASS")

    console.rule(f"[bold]{server_name}[/bold]")
    console.print(f"\n[bold]Results: {passed}/{total} passed[/bold]\n")

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Task", style="cyan", no_wrap=True)
    table.add_column("Status")
    table.add_column("Calls", justify="right")
    table.add_column("Answer")

    for r in scored:
        answer = r["answer"]
        if answer.startswith("ERROR:"):
            match = re.search(r"'message': '([^']+)'", answer)
            raw = " ".join((match.group(1) if match else answer[7:]).splitlines())
            truncated = raw[:80]
            if len(raw) > 80:
                last_space = truncated.rfind(" ")
                if last_space > 40:
                    truncated = truncated[:last_space] + "..."
                else:
                    truncated = truncated[:80] + "..."
            answer_cell = Text(truncated, style="bold red")
        else:
            flat = " ".join(answer.splitlines())
            truncated = flat[:80]
            if len(flat) > 80:
                last_space = truncated.rfind(" ")
                if last_space > 40:
                    truncated = truncated[:last_space] + "..."
                else:
                    truncated = truncated[:80] + "..."
            answer_cell = truncated

        table.add_row(r["id"], _status_cell(r["status"]), str(r["call_count"]), answer_cell)

    console.print(table)

    if verbose:
        for r in scored:
            if not r["answer"].startswith("ERROR:"):
                for msg in r["failed"]:
                    console.print(f"  [bold red]FAIL ({r['id']}): {msg}[/bold red]")
            for msg in r["passed"]:
                console.print(f"  [dim green]pass ({r['id']}): {msg}[/dim green]")

        console.print()
        console.print("[bold]Answers:[/bold]")
        for r in scored:
            console.print(f"  [cyan]{r['id']}:[/cyan]")
            answer = r["answer"]
            if answer.startswith("ERROR:"):
                match = re.search(r"'message': '([^']+)'", answer)
                text = match.group(1) if match else answer[7:]
                for line in text.splitlines():
                    console.print(f"    [bold red]{line}[/bold red]")
            else:
                for line in answer.splitlines():
                    console.print(f"    {line}")

    console.print()


def print_verdicts(verdicts: list, judge_model: str):
    console.rule(f"[bold]Judge Verdicts[/bold] [dim]({judge_model})[/dim]")
    console.print()

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Task", style="cyan", no_wrap=True)
    table.add_column("Verdict")
    table.add_column("Reason")

    for v in verdicts:
        table.add_row(v["id"], _verdict_cell(v["verdict"]), v.get("reason", ""))

    console.print(table)
    console.print()


def _compare_cell(r: dict | None) -> Text:
    if r is None:
        return Text("FAIL", style="red")
    status_styles = {
        "PASS": ("✓ PASS", "green"),
        "FAIL": ("✗ FAIL", "red"),
        "PARTIAL": ("~ PARTIAL", "blue"),
        "WARN": ("! WARN", "yellow"),
        "ERROR": ("! ERROR", "yellow"),
    }
    label, style = status_styles.get(r["status"], (r["status"], "white"))
    return Text(f"{label} ({r['call_count']})", style=style)


def print_compare_table(scored1: list, scored2: list, server1_name: str, server2_name: str):
    scored2_by_id = {r["id"]: r for r in scored2}

    console.rule("[bold]Comparison[/bold]")
    console.print()

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Task", style="cyan", no_wrap=True)
    table.add_column(server1_name, justify="center")
    table.add_column(server2_name, justify="center")

    for r1 in scored1:
        r2 = scored2_by_id.get(r1["id"])
        table.add_row(r1["id"], _compare_cell(r1), _compare_cell(r2))

    console.print(table)
    console.print()
