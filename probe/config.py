import os
from pathlib import Path
import yaml

DEFAULT_AGENT_MODEL = "claude-haiku-4-5"
DEFAULT_JUDGE_MODEL = "claude-haiku-4-5"
DEFAULT_RESULTS_DIR = "results"
DEFAULT_JUDGE_DIR = "judge"

CONFIG_FILE = "probe.yaml"


def load_config() -> dict:
    """Load probe.yaml if it exists, otherwise return defaults."""
    config = {
        "models": {
            "agent": DEFAULT_AGENT_MODEL,
            "judge": DEFAULT_JUDGE_MODEL,
        },
        "output": {
            "results_dir": DEFAULT_RESULTS_DIR,
            "judge_dir": DEFAULT_JUDGE_DIR,
        },
    }

    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        return config

    with open(config_path) as f:
        user_config = yaml.safe_load(f)

    if not user_config:
        return config

    if "models" in user_config:
        if "agent" in user_config["models"]:
            config["models"]["agent"] = user_config["models"]["agent"]
        if "judge" in user_config["models"]:
            config["models"]["judge"] = user_config["models"]["judge"]

    if "output" in user_config:
        if "results_dir" in user_config["output"]:
            config["output"]["results_dir"] = user_config["output"]["results_dir"]
        if "judge_dir" in user_config["output"]:
            config["output"]["judge_dir"] = user_config["output"]["judge_dir"]

    return config


def get_agent_model(config: dict) -> str:
    return config["models"]["agent"]


def get_judge_model(config: dict) -> str:
    return config["models"]["judge"]


def get_results_dir(config: dict) -> str:
    return config["output"]["results_dir"]


def get_judge_dir(config: dict) -> str:
    return config["output"]["judge_dir"]
