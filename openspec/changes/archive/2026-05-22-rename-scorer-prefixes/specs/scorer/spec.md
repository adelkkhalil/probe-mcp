## MODIFIED Requirements

### Requirement: det_tools_called_includes checks for tool presence

When `expect` contains `det_tools_called_includes`, the scorer SHALL verify that each named tool appears at least once in the trace. A tool found in the trace goes to `passed`; a tool not found goes to `failed`.

#### Scenario: Required tool was called

- **WHEN** `expect["det_tools_called_includes"]` contains `"get_orders"` and the trace includes a call to `"get_orders"`
- **THEN** `"tool 'get_orders' was called"` appears in `"passed"`

#### Scenario: Required tool was not called

- **WHEN** `expect["det_tools_called_includes"]` contains `"get_orders"` and the trace has no call to `"get_orders"`
- **THEN** `"tool 'get_orders' was NOT called"` appears in `"failed"`

---

### Requirement: det_max_calls enforces a call count ceiling

When `expect` contains `det_max_calls`, the scorer SHALL compare the trace length against that limit. If the actual count is within the limit it goes to `passed`; if it exceeds the limit it goes to `failed`.

#### Scenario: Call count within limit

- **WHEN** `expect["det_max_calls"]` is `5` and the trace has 3 entries
- **THEN** a message confirming the call count is within the limit appears in `"passed"`

#### Scenario: Call count exceeds limit

- **WHEN** `expect["det_max_calls"]` is `2` and the trace has 5 entries
- **THEN** a message indicating the limit was exceeded appears in `"failed"`

---

### Requirement: det_answer_includes performs case-insensitive substring check

When `expect` contains `det_answer_includes`, the scorer SHALL check whether the substring appears in the final answer using a case-insensitive comparison.

#### Scenario: Substring present in answer

- **WHEN** `expect["det_answer_includes"]` is `"Germany"` and `answer` contains `"germany"` (lowercase)
- **THEN** `"passed"` includes a message confirming the substring was found

#### Scenario: Substring absent from answer

- **WHEN** `expect["det_answer_includes"]` is `"Germany"` and `answer` does not contain it in any case
- **THEN** `"failed"` includes a message indicating the substring was missing
