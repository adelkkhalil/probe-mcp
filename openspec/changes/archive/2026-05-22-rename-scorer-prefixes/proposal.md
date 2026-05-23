## Why

The scorer's three expectation keys (`tools_called_includes`, `max_calls`, `answer_includes`) have no naming signal distinguishing them from future semantic/LLM-judged keys. Prefixing them with `det_` makes the deterministic nature of each check self-documenting at the YAML level, and reserves unprefixed or differently-prefixed namespaces for future key families without a breaking change later.

## What Changes

- `tools_called_includes` → `det_tools_called_includes` in scorer logic, all task YAML files, CLI docs, README, and specs
- `max_calls` → `det_max_calls` in the same locations
- `answer_includes` → `det_answer_includes` in the same locations
- The `--ignore-tool-names` flag (which pops `tools_called_includes`) must pop `det_tools_called_includes` instead
- **BREAKING**: Any task YAML using the old key names will silently produce zero checks (keys are unrecognized). Authors must rename keys.

## Capabilities

### New Capabilities

_(none — this is a rename-only change)_

### Modified Capabilities

- `scorer`: requirement names and scenario examples reference the old key names; all three expectation-key requirements need their identifiers, scenario text, and field references updated to the `det_` prefix

## Impact

- `probe/scorer.py`: three key lookups renamed
- `probe/cli.py`: `--ignore-tool-names` pops `det_tools_called_includes`; any `--help` text mentioning key names
- `tasks/*.yaml`: every `expect:` block using any of the three old keys
- `openspec/specs/scorer/spec.md`: requirement headings and scenario field references
- `README.md` (expectations table / key list)
- No changes to runner, judge, reporter, loader, or config
