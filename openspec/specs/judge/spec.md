# Spec: Judge

## Purpose

The judge module performs semantic pass/fail evaluation of task results using an LLM call. It loads a prompt template from `probe/judge_prompt.txt`, formats it with task data, calls the Anthropic API, parses the JSON verdict, and saves a judge file to disk.

## Requirements

### Requirement: Prompt template must contain required placeholders

When loading `judge_prompt.txt`, the judge SHALL validate at load time that the text contains all three required placeholders: `{task_prompt}`, `{tool_trace}`, and `{answer}`. If any are missing, a `ValueError` is raised.

#### Scenario: Missing placeholder raises ValueError

- **WHEN** `judge_prompt.txt` is missing `{tool_trace}`
- **THEN** `load_judge_prompt()` raises `ValueError` with a message identifying the missing placeholder

#### Scenario: Valid prompt template loads successfully

- **WHEN** `judge_prompt.txt` contains all three required placeholders
- **THEN** `load_judge_prompt()` returns the prompt text without raising

---

### Requirement: Prompt template must declare required output fields

The judge SHALL also validate at load time that the prompt text contains the strings `"verdict"` and `"reason"` as output field references. Missing either raises a `ValueError`.

#### Scenario: Missing output field raises ValueError

- **WHEN** `judge_prompt.txt` does not contain `"verdict"`
- **THEN** `load_judge_prompt()` raises `ValueError` mentioning the missing field

---

### Requirement: Tool trace is formatted as numbered lines

The judge SHALL format the trace list into a human-readable string where each call is a numbered line in the form `N. tool_name(key=value, ...)`. An empty trace formats to the literal string `"(no tools called)"`.

#### Scenario: Non-empty trace formats as numbered list

- **WHEN** the trace is `[{"tool": "get_orders", "params": {"limit": 5}}]`
- **THEN** `format_tool_trace(trace)` returns `"1. get_orders(limit=5)"`

#### Scenario: Empty trace returns placeholder string

- **WHEN** the trace is an empty list
- **THEN** `format_tool_trace([])` returns `"(no tools called)"`

---

### Requirement: LLM judge is called with the formatted prompt

The judge SHALL call `Anthropic().messages.create` with the configured judge model, `max_tokens=500`, and the assembled prompt as the sole user message.

#### Scenario: Judge API call uses specified model and token cap

- **WHEN** `judge_task()` is called with `judge_model="claude-haiku-4-5"`
- **THEN** `messages.create` is called with `model="claude-haiku-4-5"` and `max_tokens=500`

---

### Requirement: JSON response is parsed and stripped of markdown fences

The judge SHALL strip leading code fences (` ```json ` or ` ``` `) and trailing backticks from the LLM response text before parsing it as JSON.

#### Scenario: Markdown-fenced JSON is parsed correctly

- **WHEN** the LLM returns a response wrapped in ` ```json ` fences
- **THEN** `judge_task()` successfully parses the JSON and returns the verdict

---

### Requirement: Verdict is constrained to valid values

Valid verdict values are `PASS`, `PARTIAL`, `FAIL`, and `ERROR`. Any verdict returned by the LLM that is not in this set SHALL be coerced to `"ERROR"`.

#### Scenario: Invalid verdict is coerced to ERROR

- **WHEN** the LLM returns `{"verdict": "UNKNOWN", "reason": "..."}`
- **THEN** the returned verdict is `"ERROR"`

#### Scenario: Valid verdict is preserved

- **WHEN** the LLM returns `{"verdict": "PARTIAL", "reason": "..."}`
- **THEN** the returned verdict is `"PARTIAL"`

---

### Requirement: Judge exceptions return ERROR verdict

If calling the LLM or parsing the response raises any exception, the judge SHALL return `{"verdict": "ERROR", "reason": "Judge failed: <message>"}` without propagating the exception.

#### Scenario: API exception yields ERROR verdict

- **WHEN** `messages.create` raises an exception
- **THEN** `judge_task()` returns a dict with `"verdict": "ERROR"` and a reason starting with `"Judge failed:"`

---

### Requirement: Prompt version is extracted from the template comment

The judge SHALL extract the prompt version from the comment line `# prompt_version: <value>` in `judge_prompt.txt` and store it in the judge file's `meta` object.

#### Scenario: Prompt version appears in judge file meta

- **WHEN** `judge_prompt.txt` contains `# prompt_version: 1.0`
- **THEN** the saved judge file's `meta.prompt_version` is `"1.0"`

---

### Requirement: Judge file is saved with a deterministic naming convention

After judging all results, the judge SHALL save a JSON file to the configured judge directory. The filename MUST follow the pattern `{results_stem}_judge_{judge_model}_{run_id}.json` where `run_id` is a 4-character hex token.

#### Scenario: Judge file name follows the convention

- **WHEN** `judge_results_file("results/server_2024-01-01_12-00_claude-haiku-4-5_abcd.json", ...)` completes
- **THEN** a file is created in `judge_dir/` named `server_2024-01-01_12-00_claude-haiku-4-5_abcd_judge_<model>_<4hex>.json`

---

### Requirement: Judge file contains meta and verdicts

The saved judge file SHALL contain a `"meta"` object (with `results_file`, `judge_model`, `prompt_version`, `timestamp`, `run_id`) and a `"verdicts"` list with one entry per task.

#### Scenario: Judge file structure is correct

- **WHEN** the judge file is loaded from disk
- **THEN** it has a `"meta"` key and a `"verdicts"` key, and each verdict entry has `"id"`, `"verdict"`, and `"reason"`

---

### Requirement: Judge directory is created if absent

The judge SHALL create the judge directory (including parent directories) if it does not exist before writing the file.

#### Scenario: Missing judge directory is created automatically

- **WHEN** the configured judge directory does not exist
- **THEN** `judge_results_file()` creates the directory and writes the file successfully

---

### Requirement: judge_results_file mirrors per-task progress to log_console when provided

When `judge_results_file` is called with a non-None `log_console` parameter, it SHALL write each per-task "Judged: {id} → {verdict}" progress line to `log_console` in addition to the module's internal console. When `log_console` is `None`, behaviour is identical to before.

#### Scenario: Judged progress lines appear in log file when log_console is provided

- **WHEN** `judge_results_file(results_path, model, judge_dir, log_console=lc)` is called
- **THEN** each `Judged: <task_id> → <verdict>` line is written to both the terminal console and `lc`

#### Scenario: judge_results_file is unchanged when log_console is None

- **WHEN** `judge_results_file(results_path, model, judge_dir)` is called without `log_console`
- **THEN** output goes only to the module's internal console, identical to previous behaviour

---

### Requirement: Missing or invalid results file raises an exception

If the results file path does not exist, the judge SHALL raise `FileNotFoundError`. If the file contains invalid JSON, the judge SHALL raise `ValueError`.

#### Scenario: Missing results file raises FileNotFoundError

- **WHEN** `results_path` does not exist on disk
- **THEN** `judge_results_file()` raises `FileNotFoundError`

#### Scenario: Invalid JSON results file raises ValueError

- **WHEN** the results file contains malformed JSON
- **THEN** `judge_results_file()` raises `ValueError`
