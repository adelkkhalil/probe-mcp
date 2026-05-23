## MODIFIED Requirements

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

### Requirement: Scored result contains required fields

The scorer SHALL always return a dict containing `"id"`, `"status"`, `"passed"`, `"failed"`, `"call_count"`, `"answer"`, `"det_score"`, and `"pro_score"`. Non-error results additionally include `"expect"` and `"trace"`.

#### Scenario: Non-error scored result has all required fields

- **WHEN** `score_task(result)` is called with a non-error result
- **THEN** the returned dict has keys `"id"`, `"status"`, `"passed"`, `"failed"`, `"call_count"`, `"answer"`, `"expect"`, `"trace"`, `"det_score"`, and `"pro_score"`

#### Scenario: call_count reflects trace length

- **WHEN** the trace has 4 entries
- **THEN** `"call_count"` in the scored dict is `4`

---

## ADDED Requirements

### Requirement: det_score summarises deterministic check counts

The scorer SHALL populate `det_score` as a dict with `"passed"` (count of checks that passed) and `"total"` (count of all deterministic checks evaluated). When no `deterministic` sub-dict is present in `expect`, both values SHALL be `0`.

#### Scenario: All deterministic checks pass

- **WHEN** two `tools_called_includes` checks both pass and no other checks are declared
- **THEN** `det_score` is `{"passed": 2, "total": 2}`

#### Scenario: No deterministic section

- **WHEN** `expect` has no `deterministic` key
- **THEN** `det_score` is `{"passed": 0, "total": 0}`

---

### Requirement: pro_score reflects probabilistic section intent

The scorer SHALL populate `pro_score` as `"pending"` when `expect["probabilistic"]["judge"]` is `true`, and `null` when no `probabilistic` section is present. The scorer does not run the judge; it only records the declared intent.

#### Scenario: Judge declared in probabilistic section

- **WHEN** `expect["probabilistic"]["judge"]` is `true`
- **THEN** `pro_score` in the scored result is `"pending"`

#### Scenario: No probabilistic section

- **WHEN** `expect` has no `probabilistic` key
- **THEN** `pro_score` in the scored result is `null`
