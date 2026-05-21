# Spec: Config

## Purpose

The config module loads `probe.yaml` from the current directory and merges user-supplied values over hardcoded defaults. It exposes typed accessor functions that the rest of the codebase uses to read model names, token limits, and output directories.

## Requirements

### Requirement: Default values when config file is absent

When `probe.yaml` does not exist the module SHALL return a config dict populated entirely with hardcoded defaults: agent model `claude-haiku-4-5`, judge model `claude-haiku-4-5`, max_tokens `4096`, results_dir `results`, and judge_dir `judge`.

#### Scenario: Missing probe.yaml returns defaults

- **WHEN** `probe.yaml` does not exist in the current directory
- **THEN** `load_config()` returns a dict with `models.agent == "claude-haiku-4-5"`, `models.judge == "claude-haiku-4-5"`, `max_tokens == 4096`, `output.results_dir == "results"`, and `output.judge_dir == "judge"`

---

### Requirement: Shallow per-key override from probe.yaml

When `probe.yaml` exists and contains valid YAML, the module SHALL apply a shallow per-key merge: only the keys present in the file override defaults; absent keys retain their default values.

#### Scenario: Partial probe.yaml overrides only specified keys

- **WHEN** `probe.yaml` contains only `models.agent: claude-sonnet-4-6`
- **THEN** `get_agent_model(config)` returns `"claude-sonnet-4-6"`, `get_judge_model(config)` returns the default `"claude-haiku-4-5"`, and `get_max_tokens(config)` returns `4096`

#### Scenario: Full probe.yaml overrides all keys

- **WHEN** `probe.yaml` sets all four config sections
- **THEN** each accessor returns the user-supplied value, not the default

---

### Requirement: Malformed YAML causes process exit

When `probe.yaml` exists but contains invalid YAML, the module SHALL write an error message to stderr and exit with a non-zero status code rather than propagating an exception.

#### Scenario: Invalid YAML triggers stderr message and exit

- **WHEN** `probe.yaml` contains YAML that fails to parse
- **THEN** an error message is written to `sys.stderr` mentioning `probe.yaml` and `sys.exit(1)` is called

---

### Requirement: Empty probe.yaml falls back to defaults

When `probe.yaml` exists but is empty or evaluates to `None` after parsing, the module SHALL return the full default config without error.

#### Scenario: Empty file yields defaults

- **WHEN** `probe.yaml` is a zero-byte file
- **THEN** `load_config()` returns defaults for all keys

---

### Requirement: Typed accessor functions

Callers MUST retrieve config values through `get_agent_model`, `get_judge_model`, `get_max_tokens`, `get_results_dir`, and `get_judge_dir`. Each accessor SHALL accept the config dict and return the corresponding typed value.

#### Scenario: Accessor returns correct type

- **WHEN** `config` is the dict returned by `load_config()`
- **THEN** `get_agent_model(config)` returns a `str`, `get_judge_model(config)` returns a `str`, `get_max_tokens(config)` returns an `int`, `get_results_dir(config)` returns a `str`, and `get_judge_dir(config)` returns a `str`

---

### Requirement: max_tokens override

When `probe.yaml` contains a `max_tokens` key, the module SHALL use that value instead of the default `4096`.

#### Scenario: Custom max_tokens is applied

- **WHEN** `probe.yaml` sets `max_tokens: 8192`
- **THEN** `get_max_tokens(config)` returns `8192`

---

### Requirement: Directory config override

When `probe.yaml` contains `output.results_dir` or `output.judge_dir`, those values SHALL override the defaults `results` and `judge` respectively.

#### Scenario: Custom output directories are applied

- **WHEN** `probe.yaml` sets `output.results_dir: my_results` and `output.judge_dir: my_judge`
- **THEN** `get_results_dir(config)` returns `"my_results"` and `get_judge_dir(config)` returns `"my_judge"`
