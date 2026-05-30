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

When `expect["deterministic"]` contains `tools_called_includes`, the scorer SHALL verify that each named tool appears at least once in the trace. A tool found in the trace goes to `passed`; a tool not found goes to `failed`.

#### Scenario: Required tool was called

- **WHEN** `expect["deterministic"]["tools_called_includes"]` contains `"get_orders"` and the trace includes a call to `"get_orders"`
- **THEN** `"tool 'get_orders' was called"` appears in `"passed"`

#### Scenario: Required tool was not called

- **WHEN** `expect["deterministic"]["tools_called_includes"]` contains `"get_orders"` and the trace has no call to `"get_orders"`
- **THEN** `"tool 'get_orders' was NOT called"` appears in `"failed"`

---

### Requirement: max_calls enforces a call count ceiling

When `expect["deterministic"]` contains `max_calls`, the scorer SHALL compare the trace length against that limit. If the actual count is within the limit it goes to `passed`; if it exceeds the limit it goes to `failed`.

#### Scenario: Call count within limit

- **WHEN** `expect["deterministic"]["max_calls"]` is `5` and the trace has 3 entries
- **THEN** a message confirming the call count is within the limit appears in `"passed"`

#### Scenario: Call count exceeds limit

- **WHEN** `expect["deterministic"]["max_calls"]` is `2` and the trace has 5 entries
- **THEN** a message indicating the limit was exceeded appears in `"failed"`

---

### Requirement: answer_includes performs case-insensitive substring check

When `expect["deterministic"]` contains `answer_includes`, the scorer SHALL check whether the substring appears in the final answer using a case-insensitive comparison.

#### Scenario: Substring present in answer

- **WHEN** `expect["deterministic"]["answer_includes"]` is `"Germany"` and `answer` contains `"germany"` (lowercase)
- **THEN** `"passed"` includes a message confirming the substring was found

#### Scenario: Substring absent from answer

- **WHEN** `expect["deterministic"]["answer_includes"]` is `"Germany"` and `answer` does not contain it in any case
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

The scorer SHALL always return a dict containing `"id"`, `"status"`, `"passed"`, `"failed"`, `"call_count"`, `"answer"`, `"det_score"`, and `"pro_score"`. Non-error results additionally include `"expect"` and `"trace"`.

#### Scenario: Non-error scored result has all required fields

- **WHEN** `score_task(result)` is called with a non-error result
- **THEN** the returned dict has keys `"id"`, `"status"`, `"passed"`, `"failed"`, `"call_count"`, `"answer"`, `"expect"`, `"trace"`, `"det_score"`, and `"pro_score"`

#### Scenario: call_count reflects trace length

- **WHEN** the trace has 4 entries
- **THEN** `"call_count"` in the scored dict is `4`

---

### Requirement: det_score summarises deterministic check counts

The scorer SHALL populate `det_score` as a dict with `"passed"` (count of checks that passed) and `"total"` (count of all deterministic checks evaluated). When no `deterministic` sub-dict is present in `expect`, both values SHALL be `0`.

#### Scenario: All deterministic checks pass

- **WHEN** two `tools_called_includes` checks both pass and no other checks are declared
- **THEN** `det_score` is `{"passed": 2, "total": 2}`

#### Scenario: No deterministic section

- **WHEN** `expect` has no `deterministic` key
- **THEN** `det_score` is `{"passed": 0, "total": 0}`

---

### Requirement: tools_called_excludes fails if any excluded tool was called

When `expect["deterministic"]` contains `tools_called_excludes`, the scorer SHALL verify that none of the listed tools appear in the trace. Each tool found in the trace goes to `failed`; each tool not found goes to `passed`.

#### Scenario: Excluded tool was not called

- **WHEN** `expect["deterministic"]["tools_called_excludes"]` contains `"get_transaction_history"` and the trace has no call to `"get_transaction_history"`
- **THEN** `"tool 'get_transaction_history' was correctly not called"` appears in `"passed"`

#### Scenario: Excluded tool was called

- **WHEN** `expect["deterministic"]["tools_called_excludes"]` contains `"get_transaction_history"` and the trace includes a call to `"get_transaction_history"`
- **THEN** `"tool 'get_transaction_history' was called but should NOT have been"` appears in `"failed"`

---

### Requirement: tool_called_count checks for exact call count

When `expect["deterministic"]` contains `tool_called_count`, the scorer SHALL compare the trace length against the exact expected value. If the actual count equals the expected count it goes to `passed`; any deviation goes to `failed`.

#### Scenario: Exact call count matches

- **WHEN** `expect["deterministic"]["tool_called_count"]` is `1` and the trace has exactly 1 entry
- **THEN** `"call count 1 matches expected 1"` appears in `"passed"`

#### Scenario: Actual count differs from expected

- **WHEN** `expect["deterministic"]["tool_called_count"]` is `1` and the trace has 3 entries
- **THEN** `"call count 3 does not match expected 1"` appears in `"failed"`

---

### Requirement: tool_params_include checks that a named tool was called with required parameter keys

When `expect["deterministic"]` contains `tool_params_include` (a dict with `tool` and `params` keys), the scorer SHALL verify that at least one call to the named tool in the trace included all listed parameter keys. If any call satisfies this the check goes to `passed`; if no call does (or the tool was never called) it goes to `failed`.

#### Scenario: Named tool called with all required parameter keys

- **WHEN** `expect["deterministic"]["tool_params_include"]` is `{"tool": "get_account", "params": ["iban"]}` and the trace contains a call to `"get_account"` with `{"iban": "AE07..."}` in params
- **THEN** a message confirming `"get_account"` was called with `["iban"]` appears in `"passed"`

#### Scenario: Named tool called but missing a required parameter key

- **WHEN** `expect["deterministic"]["tool_params_include"]` is `{"tool": "get_account", "params": ["iban"]}` and the trace contains a call to `"get_account"` with no `"iban"` key in params
- **THEN** a message indicating `"get_account"` was not called with `["iban"]` appears in `"failed"`

#### Scenario: Named tool was never called

- **WHEN** `expect["deterministic"]["tool_params_include"]["tool"]` is `"get_account"` and the trace contains no call to `"get_account"`
- **THEN** a message indicating `"get_account"` was never called appears in `"failed"`

---

### Requirement: answer_excludes fails if the string appears in the answer

When `expect["deterministic"]` contains `answer_excludes`, the scorer SHALL check whether the string appears in the final answer using a case-insensitive comparison. If found it goes to `failed`; if not found it goes to `passed`.

#### Scenario: Excluded string is absent from answer

- **WHEN** `expect["deterministic"]["answer_excludes"]` is `"AE07033123456789012345678"` and the answer does not contain it
- **THEN** `"passed"` includes a message confirming the string was absent

#### Scenario: Excluded string is present in answer

- **WHEN** `expect["deterministic"]["answer_excludes"]` is `"AE07033123456789012345678"` and the answer contains it (any case)
- **THEN** `"failed"` includes a message indicating the forbidden string was found

---

### Requirement: no_error fails if any tool call in the trace returned an error

When `expect["deterministic"]` contains `no_error: true`, the scorer SHALL check whether any trace entry has `"error": true`. If all entries have `"error": false` (or the trace is empty) it goes to `passed`; if one or more entries errored it goes to `failed`.

#### Scenario: All tool calls succeeded

- **WHEN** `expect["deterministic"]["no_error"]` is `true` and all trace entries have `"error": false`
- **THEN** `"no tool errors"` appears in `"passed"`

#### Scenario: At least one tool call returned an error

- **WHEN** `expect["deterministic"]["no_error"]` is `true` and one trace entry has `"error": true`
- **THEN** a message indicating the number of errored tool calls appears in `"failed"`

#### Scenario: Empty trace with no_error passes

- **WHEN** `expect["deterministic"]["no_error"]` is `true` and the trace is empty
- **THEN** `"no tool errors"` appears in `"passed"`

---

### Requirement: tools_called_sequence checks tool call order

When `expect["deterministic"]` contains `tools_called_sequence`, the scorer SHALL verify that the listed tools appear in the trace in the given relative order (subsequence match — other tools may appear between them). The check passes as a whole if the full sequence is satisfied; it fails if any tool in the sequence cannot be found after the previous one.

#### Scenario: Tools called in the required order

- **WHEN** `expect["deterministic"]["tools_called_sequence"]` is `["shippers", "orders"]` and the trace contains `"shippers"` at index 0 and `"orders"` at index 2
- **THEN** a message confirming the sequence was followed appears in `"passed"`

#### Scenario: Tools called in the wrong order

- **WHEN** `expect["deterministic"]["tools_called_sequence"]` is `["shippers", "orders"]` and `"orders"` appears before `"shippers"` in the trace
- **THEN** a message indicating the sequence was violated appears in `"failed"`

#### Scenario: A tool in the sequence was never called

- **WHEN** `expect["deterministic"]["tools_called_sequence"]` is `["shippers", "orders"]` and `"shippers"` is never in the trace
- **THEN** a message indicating the sequence was violated appears in `"failed"`

---

### Requirement: consistency_score summarises trial agreement

When a result dict contains a `"trials"` list (produced when `trials > 1`), the scorer SHALL compute a `consistency_score` as the fraction of trials whose PASS/FAIL status agrees with the majority status across all trials. The value is a float in `[0.0, 1.0]` where 1.0 means all trials agree. For result dicts without a `"trials"` key, no `consistency_score` is added.

#### Scenario: All trials pass

- **WHEN** all 3 trials produce a PASS result
- **THEN** `consistency_score` is `1.0`

#### Scenario: Mixed trial verdicts

- **WHEN** 2 of 3 trials produce PASS and 1 produces FAIL
- **THEN** `consistency_score` is approximately `0.67` (2/3)

#### Scenario: Single trial

- **WHEN** `trials` is 1 (or not set)
- **THEN** no `consistency_score` field is added to the scored result

---

### Requirement: pro_score reflects probabilistic section intent

The scorer SHALL populate `pro_score` as `"pending"` when `expect["probabilistic"]["judge"]` is `true`, and `null` when no `probabilistic` section is present. The scorer does not run the judge; it only records the declared intent.

#### Scenario: Judge declared in probabilistic section

- **WHEN** `expect["probabilistic"]["judge"]` is `true`
- **THEN** `pro_score` in the scored result is `"pending"`

#### Scenario: No probabilistic section

- **WHEN** `expect` has no `probabilistic` key
- **THEN** `pro_score` in the scored result is `null`
