## 1. Scorer Core

- [ ] 1.1 In `probe/scorer.py`, rename key lookup `"tools_called_includes"` → `"det_tools_called_includes"` (two references: `in expect` check and `for tool in expect[...]` iteration)
- [ ] 1.2 In `probe/scorer.py`, rename key lookup `"max_calls"` → `"det_max_calls"` (three references: `in expect` check and both `expect['max_calls']` usages)
- [ ] 1.3 In `probe/scorer.py`, rename key lookup `"answer_includes"` → `"det_answer_includes"` (three references: `in expect` check and both `expect['answer_includes']` usages)

## 2. CLI Updates

- [ ] 2.1 In `probe/cli.py`, update both `pop("tools_called_includes", None)` calls in the `eval` command to `pop("det_tools_called_includes", None)`
- [ ] 2.2 In `probe/cli.py`, update both `pop("tools_called_includes", None)` calls in the `full` command to `pop("det_tools_called_includes", None)`
- [ ] 2.3 In `probe/cli.py`, update the inline YAML example in the `--help` docstring (lines ~83-85) to use `det_tools_called_includes`, `det_max_calls`, `det_answer_includes`

## 3. Task YAML Files

- [ ] 3.1 In `tasks/northwind.yaml`, rename all `tools_called_includes:` keys to `det_tools_called_includes:`
- [ ] 3.2 In `tasks/northwind.yaml`, rename all `max_calls:` keys to `det_max_calls:`
- [ ] 3.3 In `tasks/northwind.yaml`, rename all `answer_includes:` keys to `det_answer_includes:`
- [ ] 3.4 In `tasks/my_server.yaml`, rename `tools_called_includes:`, `max_calls:`, and `answer_includes:` to their `det_` prefixed equivalents

## 4. Specs and Documentation

- [ ] 4.1 In `openspec/specs/scorer/spec.md`, update the three requirement headings from `tools_called_includes`, `max_calls`, `answer_includes` to `det_tools_called_includes`, `det_max_calls`, `det_answer_includes` and update all scenario field references accordingly
- [ ] 4.2 In `README.md`, update the expectations table / key list to use the `det_` prefixed names
