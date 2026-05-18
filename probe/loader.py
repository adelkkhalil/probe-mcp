from pathlib import Path

import yaml


def load_tasks(path: str) -> dict:
    """Load and validate a task file. Returns the parsed task suite"""
    file = Path(path)

    if not file.exists():
        raise FileNotFoundError(f"Task file not found: {path}")

    if not file.suffix == ".yaml":
        raise ValueError(f"Task file must be a .yaml file, got: {path}")

    with open(file) as f:
        data = yaml.safe_load(f)

    if "tasks" not in data:
        raise ValueError("Task file must contain a 'tasks' key")

    if "server" not in data:
        raise ValueError("Task file must contain a 'server' key")

    return data
