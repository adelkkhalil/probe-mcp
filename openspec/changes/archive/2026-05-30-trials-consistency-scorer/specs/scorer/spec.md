## ADDED Requirements

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
