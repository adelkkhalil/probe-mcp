import warnings
from pathlib import Path

import yaml


def load_tasks(path: str) -> dict:
    """Load and validate a task file. Returns the parsed task suite."""
    file = Path(path)

    if not file.exists():
        raise FileNotFoundError(f"Task file not found: {path}")

    if not file.suffix == ".yaml":
        raise ValueError(f"Task file must be a .yaml file, got: {path}")

    try:
        with open(file) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Task file is not valid YAML ({path}): {e}")

    if not isinstance(data, dict):
        raise ValueError(f"Task file must contain a YAML mapping at the top level ({path})")

    if "server" not in data:
        raise ValueError("Task file must contain a 'server' key")
    if not isinstance(data["server"], str) or not data["server"].strip():
        raise ValueError("'server' must be a non-empty string")

    if "tasks" not in data:
        raise ValueError("Task file must contain a 'tasks' key")
    if not isinstance(data["tasks"], list) or not data["tasks"]:
        raise ValueError("'tasks' must be a non-empty list")

    seen_ids: set[str] = set()
    for i, task in enumerate(data["tasks"]):
        where = f"Task #{i + 1}"
        if not isinstance(task, dict):
            raise ValueError(f"{where}: must be a YAML mapping")

        if "id" not in task or not isinstance(task["id"], str) or not task["id"].strip():
            raise ValueError(f"{where}: missing or empty string 'id'")
        task_id = task["id"]
        where = f"Task '{task_id}'"
        if task_id in seen_ids:
            raise ValueError(f"{where}: duplicate task id")
        seen_ids.add(task_id)

        if "prompt" not in task or not isinstance(task["prompt"], str) or not task["prompt"].strip():
            raise ValueError(f"{where}: missing or empty string 'prompt'")

        if "expect" not in task or not isinstance(task["expect"], dict):
            raise ValueError(f"{where}: missing dict 'expect'")

        expect = task["expect"]

        if "deterministic" in expect and not isinstance(expect["deterministic"], dict):
            raise ValueError(f"{where}: 'expect.deterministic' must be a dict")
        if "probabilistic" in expect and not isinstance(expect["probabilistic"], dict):
            raise ValueError(f"{where}: 'expect.probabilistic' must be a dict")

        if isinstance(expect.get("probabilistic"), dict):
            if "judge" in expect["probabilistic"] and not isinstance(
                expect["probabilistic"]["judge"], bool
            ):
                raise ValueError(f"{where}: 'expect.probabilistic.judge' must be a boolean")

        det = expect.get("deterministic", {})
        if "tools_called_includes" in det:
            value = det["tools_called_includes"]
            if not isinstance(value, list) or not all(isinstance(t, str) for t in value):
                raise ValueError(
                    f"{where}: 'expect.deterministic.tools_called_includes' must be a list of strings"
                )
        if "max_calls" in det:
            value = det["max_calls"]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(
                    f"{where}: 'expect.deterministic.max_calls' must be a non-negative integer"
                )
        if "answer_includes" in det:
            if not isinstance(det["answer_includes"], str):
                raise ValueError(
                    f"{where}: 'expect.deterministic.answer_includes' must be a string"
                )

        _LEGACY_KEYS = {"tools_called_includes", "max_calls", "answer_includes"}
        flat_keys = _LEGACY_KEYS & set(expect)
        if flat_keys:
            key_list = ", ".join(sorted(flat_keys))
            warnings.warn(
                f"Task '{task_id}': expect keys [{key_list}] should be nested under"
                " 'expect.deterministic'",
                UserWarning,
                stacklevel=2,
            )

    return data
