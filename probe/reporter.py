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


def _det_cell(det_score: dict) -> str:
    return f"{det_score['passed']}/{det_score['total']}"


def _consistency_cell(consistency_score: float) -> Text:
    pct = round(consistency_score * 100)
    label = f"{pct}%"
    if consistency_score >= 1.0:
        return Text(label, style="bold green")
    elif consistency_score > 0.5:
        return Text(label, style="bold yellow")
    else:
        return Text(label, style="bold red")


def _pro_cell(pro_score, task_id: str, verdicts: dict | None) -> Text:
    if pro_score is None:
        return Text("—", style="dim")
    if pro_score == "pending":
        if verdicts and task_id in verdicts:
            return _pro_cell(verdicts[task_id], task_id, None)
        return Text("—", style="dim")
    mapping = {
        "PASS": ("✓ PASS (judge)", "bold green"),
        "PARTIAL": ("~ PARTIAL (judge)", "bold blue"),
        "FAIL": ("✗ FAIL (judge)", "bold red"),
        "ERROR": ("! ERROR (judge)", "bold yellow"),
    }
    label, style = mapping.get(pro_score, (f"{pro_score} (judge)", "white"))
    return Text(label, style=style)


def print_results(
    scored: list,
    server_name: str,
    verbose: bool = False,
    verdicts: dict | None = None,
    log_console: Console | None = None,
):
    def _print(*args, **kw):
        console.print(*args, **kw)
        if log_console:
            log_console.print(*args, **kw)

    def _rule(*args, **kw):
        console.rule(*args, **kw)
        if log_console:
            log_console.rule(*args, **kw)

    total = len(scored)
    passed = sum(1 for r in scored if r["status"] == "PASS")

    _rule(f"[bold]{server_name}[/bold]")
    _print(f"\n[bold]Results: {passed}/{total} passed[/bold]\n")

    show_consistency = any("consistency_score" in r for r in scored)

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Task", style="cyan", no_wrap=True)
    table.add_column("Status")
    table.add_column("Det", justify="right")
    table.add_column("Pro")
    if show_consistency:
        table.add_column("Consistency", justify="right")
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

        det = r.get("det_score", {"passed": 0, "total": 0})
        row = [
            r["id"],
            _status_cell(r["status"]),
            _det_cell(det),
            _pro_cell(r.get("pro_score"), r["id"], verdicts),
        ]
        if show_consistency:
            cs = r.get("consistency_score")
            row.append(_consistency_cell(cs) if cs is not None else Text("—", style="dim"))
        row.extend([str(r["call_count"]), answer_cell])
        table.add_row(*row)

    _print(table)

    for r in scored:
        cs = r.get("consistency_score")
        if cs is not None and cs < 0.7:
            pct = round(cs * 100)
            _print(
                f"  [bold yellow]⚠ {r['id']}: consistency {pct}% — tool description may be too vague[/bold yellow]"
            )

    if verbose:
        for r in scored:
            if not r["answer"].startswith("ERROR:"):
                for msg in r["failed"]:
                    _print(f"  [bold red]FAIL ({r['id']}): {msg}[/bold red]")
            for msg in r["passed"]:
                _print(f"  [dim green]pass ({r['id']}): {msg}[/dim green]")

        _print()
        _print("[bold]Answers:[/bold]")
        for r in scored:
            _print(f"  [cyan]{r['id']}:[/cyan]")
            answer = r["answer"]
            if answer.startswith("ERROR:"):
                match = re.search(r"'message': '([^']+)'", answer)
                text = match.group(1) if match else answer[7:]
                for line in text.splitlines():
                    _print(f"    [bold red]{line}[/bold red]")
            else:
                for line in answer.splitlines():
                    _print(f"    {line}")

    _print()


def print_verdicts(verdicts: list, judge_model: str, log_console: Console | None = None):
    def _print(*args, **kw):
        console.print(*args, **kw)
        if log_console:
            log_console.print(*args, **kw)

    def _rule(*args, **kw):
        console.rule(*args, **kw)
        if log_console:
            log_console.rule(*args, **kw)

    _rule(f"[bold]Judge Verdicts[/bold] [dim]({judge_model})[/dim]")
    _print()

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Task", style="cyan", no_wrap=True)
    table.add_column("Verdict")
    table.add_column("Reason")

    for v in verdicts:
        table.add_row(v["id"], _verdict_cell(v["verdict"]), v.get("reason", ""))

    _print(table)
    _print()


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


def print_compare_table(
    scored1: list,
    scored2: list,
    server1_name: str,
    server2_name: str,
    log_console: Console | None = None,
):
    def _print(*args, **kw):
        console.print(*args, **kw)
        if log_console:
            log_console.print(*args, **kw)

    def _rule(*args, **kw):
        console.rule(*args, **kw)
        if log_console:
            log_console.rule(*args, **kw)

    scored2_by_id = {r["id"]: r for r in scored2}

    _rule("[bold]Comparison[/bold]")
    _print()

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Task", style="cyan", no_wrap=True)
    table.add_column(server1_name, justify="center")
    table.add_column(server2_name, justify="center")

    for r1 in scored1:
        r2 = scored2_by_id.get(r1["id"])
        table.add_row(r1["id"], _compare_cell(r1), _compare_cell(r2))

    _print(table)
    _print()
