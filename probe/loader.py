import os
import warnings
from pathlib import Path

import yaml


def _find_servers_yaml(task_file_path: Path) -> Path:
    """Lookup: task file directory, then its parent, then PROBE_CWD / cwd."""
    searched = []

    # 1. Task file's own directory
    candidate = task_file_path.parent / "servers.yaml"
    if candidate.exists():
        return candidate
    searched.append(candidate)

    # 2. Parent of task file's directory (project root when tasks live in tasks/)
    parent_candidate = task_file_path.parent.parent / "servers.yaml"
    if parent_candidate != candidate and parent_candidate.exists():
        return parent_candidate
    if parent_candidate != candidate:
        searched.append(parent_candidate)

    # 3. PROBE_CWD / process cwd
    probe_cwd = os.environ.get("PROBE_CWD")
    fallback_dir = Path(probe_cwd) if probe_cwd else Path.cwd()
    cwd_candidate = fallback_dir / "servers.yaml"
    if cwd_candidate not in searched and cwd_candidate.exists():
        return cwd_candidate
    if cwd_candidate not in searched:
        searched.append(cwd_candidate)

    paths = "\n".join(f"  {p}" for p in searched)
    raise FileNotFoundError(
        f"servers.yaml not found. Searched:\n{paths}\n"
        f"Run 'probe-mcp init' to create one, or add servers.yaml to your task file directory."
    )


def _load_servers(servers_yaml_path: Path) -> dict:
    """Parse and validate servers.yaml, returning the parsed servers mapping."""
    try:
        with open(servers_yaml_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"servers.yaml is not valid YAML ({servers_yaml_path}): {e}")

    if not isinstance(data, dict) or "servers" not in data:
        raise ValueError(f"servers.yaml must contain a top-level 'servers' mapping ({servers_yaml_path})")

    servers = data["servers"]
    if not isinstance(servers, dict) or not servers:
        raise ValueError(f"servers.yaml 'servers' must be a non-empty mapping ({servers_yaml_path})")

    for name, entry in servers.items():
        if not isinstance(entry, dict):
            raise ValueError(f"servers.yaml: server '{name}' must be a mapping")
        command = entry.get("command")
        if not isinstance(command, str) or not command.strip():
            raise ValueError(f"servers.yaml: server '{name}' missing non-empty 'command' string")
        args = entry.get("args")
        if args is None:
            raise ValueError(f"servers.yaml: server '{name}' missing 'args' list")
        if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
            raise ValueError(f"servers.yaml: server '{name}' 'args' must be a list of strings")

    return servers


def _resolve_server(name: str, servers: dict, servers_yaml_path: Path) -> dict:
    """Resolve a server name to its command/args/cwd dict."""
    if name not in servers:
        raise ValueError(
            f"Server '{name}' not found in {servers_yaml_path}. "
            f"Available servers: {', '.join(servers)}"
        )
    entry = servers[name]
    return {
        "name": name,
        "command": entry["command"],
        "args": entry["args"],
        "cwd": str(servers_yaml_path.parent.resolve()),
    }


def load_tasks(path: str, server_name: str) -> dict:
    """Load and validate a task file. Returns the parsed task suite.

    suite["server"] is resolved to {"name", "command", "args", "cwd"} via
    servers.yaml located in the task file's directory or PROBE_CWD.
    server_name is a required argument — it is NOT read from the task YAML.
    """
    if not server_name or not server_name.strip():
        raise ValueError("server_name must be a non-empty string")

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

    if "server" in data:
        raise ValueError(
            "Task files no longer support a 'server' field. "
            "Remove it and pass the server name via --server."
        )

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

        if "trials" in task:
            value = task["trials"]
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{where}: 'trials' must be a positive integer")

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
        if "tools_called_excludes" in det:
            value = det["tools_called_excludes"]
            if not isinstance(value, list) or not all(isinstance(t, str) for t in value):
                raise ValueError(
                    f"{where}: 'expect.deterministic.tools_called_excludes' must be a list of strings"
                )
        if "tool_called_count" in det:
            value = det["tool_called_count"]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(
                    f"{where}: 'expect.deterministic.tool_called_count' must be a non-negative integer"
                )
        if "tool_params_include" in det:
            value = det["tool_params_include"]
            if not isinstance(value, dict):
                raise ValueError(
                    f"{where}: 'expect.deterministic.tool_params_include' must be a dict"
                )
            tool_name = value.get("tool")
            if not isinstance(tool_name, str) or not tool_name.strip():
                raise ValueError(
                    f"{where}: 'expect.deterministic.tool_params_include.tool' must be a non-empty string"
                )
            params = value.get("params")
            if not isinstance(params, list) or not all(isinstance(p, str) for p in params):
                raise ValueError(
                    f"{where}: 'expect.deterministic.tool_params_include.params' must be a list of strings"
                )
        if "answer_excludes" in det:
            if not isinstance(det["answer_excludes"], str):
                raise ValueError(
                    f"{where}: 'expect.deterministic.answer_excludes' must be a string"
                )
        if "no_error" in det:
            if det["no_error"] is not True:
                raise ValueError(
                    f"{where}: 'expect.deterministic.no_error' must be boolean true"
                )
        if "tools_called_sequence" in det:
            value = det["tools_called_sequence"]
            if not isinstance(value, list) or not all(isinstance(t, str) for t in value):
                raise ValueError(
                    f"{where}: 'expect.deterministic.tools_called_sequence' must be a list of strings"
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

    # Resolve server name via servers.yaml
    servers_yaml_path = _find_servers_yaml(file)
    servers = _load_servers(servers_yaml_path)
    data["server"] = _resolve_server(server_name, servers, servers_yaml_path)

    return data
