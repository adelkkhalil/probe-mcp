## ADDED Requirements

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

When a result dict contains a `"trials"` list (produced when `trials > 1`), the scorer SHALL compute a `consistency_score` as the fraction of trials whose PASS/FAIL status agrees with the majority status across all trials. The value is a float in `[0.0, 1.0]` where 1.0 means all trials agree.

#### Scenario: All trials pass

- **WHEN** all 3 trials produce a PASS result
- **THEN** `consistency_score` is `1.0`

#### Scenario: Mixed trial verdicts

- **WHEN** 2 of 3 trials produce PASS and 1 produces FAIL
- **THEN** `consistency_score` is approximately `0.67` (2/3)

#### Scenario: Single trial

- **WHEN** `trials` is 1 (or not set)
- **THEN** `consistency_score` is `1.0` (single trial always consistent)
