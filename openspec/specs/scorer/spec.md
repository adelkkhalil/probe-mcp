# Spec: Scorer

## Purpose

The scorer performs structural pass/fail evaluation of a single task result against its declared expectations. It is a pure function that reads the result dict and returns a scored dict without performing I/O or calling the Anthropic API.

## Requirements

### Requirement: Error answers short-circuit to FAIL

If the task's `answer` starts with the literal prefix `"ERROR:"`, the scorer SHALL return status `"FAIL"` immediately with a single failed message and an empty passed list, skipping all other expectation checks.

#### Scenario: ERROR prefix yields immediate FAIL with no checks evaluated

- **WHEN** `result["answer"]` starts with `"ERROR:"`
- **THEN** the returned dict has `"status": "FAIL"`, `"passed"` is an empty list, `"failed"` contains exactly one entry beginning with `"task errored:"`, and no expectation keys are evaluated

#### Scenario: Structured error message is extracted from answer

- **WHEN** the answer contains a `'message': '<text>'` pattern
- **THEN** the failed entry extracts that text (up to 100 characters) as the error message

---

### Requirement: tools_called_includes checks for tool presence

When `expect` contains `tools_called_includes`, the scorer SHALL verify that each named tool appears at least once in the trace. A tool found in the trace goes to `passed`; a tool not found goes to `failed`.

#### Scenario: Required tool was called

- **WHEN** `expect["tools_called_includes"]` contains `"get_orders"` and the trace includes a call to `"get_orders"`
- **THEN** `"tool 'get_orders' was called"` appears in `"passed"`

#### Scenario: Required tool was not called

- **WHEN** `expect["tools_called_includes"]` contains `"get_orders"` and the trace has no call to `"get_orders"`
- **THEN** `"tool 'get_orders' was NOT called"` appears in `"failed"`

---

### Requirement: max_calls enforces a call count ceiling

When `expect` contains `max_calls`, the scorer SHALL compare the trace length against that limit. If the actual count is within the limit it goes to `passed`; if it exceeds the limit it goes to `failed`.

#### Scenario: Call count within limit

- **WHEN** `expect["max_calls"]` is `5` and the trace has 3 entries
- **THEN** a message confirming the call count is within the limit appears in `"passed"`

#### Scenario: Call count exceeds limit

- **WHEN** `expect["max_calls"]` is `2` and the trace has 5 entries
- **THEN** a message indicating the limit was exceeded appears in `"failed"`

---

### Requirement: answer_includes performs case-insensitive substring check

When `expect` contains `answer_includes`, the scorer SHALL check whether the substring appears in the final answer using a case-insensitive comparison.

#### Scenario: Substring present in answer

- **WHEN** `expect["answer_includes"]` is `"Germany"` and `answer` contains `"germany"` (lowercase)
- **THEN** `"passed"` includes a message confirming the substring was found

#### Scenario: Substring absent from answer

- **WHEN** `expect["answer_includes"]` is `"Germany"` and `answer` does not contain it in any case
- **THEN** `"failed"` includes a message indicating the substring was missing

---

### Requirement: Status is PASS only when no checks failed

The scorer SHALL set `"status"` to `"PASS"` if and only if the `failed` list is empty after evaluating all expectations. Any failure sets status to `"FAIL"`.

#### Scenario: All checks pass yields PASS status

- **WHEN** all expectation checks produce entries only in `passed`
- **THEN** `"status"` is `"PASS"`

#### Scenario: Any failed check yields FAIL status

- **WHEN** at least one expectation check produces an entry in `failed`
- **THEN** `"status"` is `"FAIL"`

---

### Requirement: Scored result contains required fields

The scorer SHALL always return a dict containing `"id"`, `"status"`, `"passed"`, `"failed"`, `"call_count"`, and `"answer"`. Non-error results additionally include `"expect"` and `"trace"`.

#### Scenario: Non-error scored result has all required fields

- **WHEN** `score_task(result)` is called with a non-error result
- **THEN** the returned dict has keys `"id"`, `"status"`, `"passed"`, `"failed"`, `"call_count"`, `"answer"`, `"expect"`, and `"trace"`

#### Scenario: call_count reflects trace length

- **WHEN** the trace has 4 entries
- **THEN** `"call_count"` in the scored dict is `4`
