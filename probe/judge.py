import json
import re
import secrets
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic
from rich.console import Console

_client = Anthropic()
_console = Console()

REQUIRED_PLACEHOLDERS = ["{task_prompt}", "{tool_trace}", "{answer}"]
REQUIRED_OUTPUT_FIELDS = ['"verdict"', '"reason"']
VALID_VERDICTS = {"PASS", "PARTIAL", "FAIL", "ERROR"}


def validate_judge_prompt(prompt_text: str):
    for placeholder in REQUIRED_PLACEHOLDERS:
        if placeholder not in prompt_text:
            raise ValueError(f"Judge prompt missing required placeholder: {placeholder}")
    for field in REQUIRED_OUTPUT_FIELDS:
        if field not in prompt_text:
            raise ValueError(f"Judge prompt missing required output field: {field}")


def load_judge_prompt() -> str:
    prompt_path = Path(__file__).parent / "judge_prompt.txt"
    text = prompt_path.read_text()
    validate_judge_prompt(text)
    return text


def format_tool_trace(trace: list) -> str:
    if not trace:
        return "(no tools called)"
    lines = []
    for i, call in enumerate(trace, 1):
        params = ", ".join(f"{k}={v}" for k, v in call.get("params", {}).items())
        lines.append(f"{i}. {call['tool']}({params})")
    return "\n".join(lines)


async def judge_task(task_id: str, task_prompt: str, trace: list, answer: str, judge_model: str) -> dict:
    prompt_template = load_judge_prompt()
    tool_trace = format_tool_trace(trace)

    prompt = prompt_template.format(
        task_prompt=task_prompt,
        tool_trace=tool_trace,
        answer=answer,
    )

    try:
        response = _client.messages.create(
            model=judge_model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        text = re.sub(r"^```(?:json)?\n?", "", text).rstrip("`").strip()
        data = json.loads(text)
        verdict = data.get("verdict", "ERROR")
        if verdict not in VALID_VERDICTS:
            verdict = "ERROR"
        reason = data.get("reason", "No reason provided")
    except Exception as e:
        verdict = "ERROR"
        reason = f"Judge failed: {str(e)[:100]}"

    return {"id": task_id, "verdict": verdict, "reason": reason}


async def judge_results_file(results_path: str, judge_model: str, judge_dir: str) -> str:
    with open(results_path) as f:
        data = json.load(f)

    results = data.get("results", [])

    prompt_text = load_judge_prompt()
    version_match = re.search(r"prompt_version:\s*(\S+)", prompt_text)
    prompt_version = version_match.group(1) if version_match else "1.0"

    verdicts = []
    for result in results:
        verdict = await judge_task(
            task_id=result["id"],
            task_prompt=result.get("prompt", ""),
            trace=result.get("trace", []),
            answer=result.get("answer", ""),
            judge_model=judge_model,
        )
        verdicts.append(verdict)
        _console.print(f"[dim]Judged: {result['id']}[/dim] → {verdict['verdict']}")

    Path(judge_dir).mkdir(parents=True, exist_ok=True)
    results_stem = Path(results_path).stem
    run_id = secrets.token_hex(2)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    filename = f"{results_stem}_judge_{judge_model}_{run_id}.json"
    filepath = Path(judge_dir) / filename

    judge_meta = {
        "results_file": Path(results_path).name,
        "judge_model": judge_model,
        "prompt_version": prompt_version,
        "timestamp": timestamp,
        "run_id": run_id,
    }

    filepath.write_text(json.dumps({"meta": judge_meta, "verdicts": verdicts}, indent=2))
    return str(filepath)
