# Example Output

```markdown
## Structured Change Brief

mode_selected: evidence freshness

Summary: Exclude closed accounts from standard monthly exports unless audit mode is enabled.

Current Behavior: Monthly exports include active and closed accounts without distinction.

Desired Behavior: Standard exports include only accounts active during the selected period.

Actor: Finance analyst.
Trigger: Analyst runs a monthly export.
Scope: Export query, export summary count, export contract documentation.
Non-Goals: No redesign of account lifecycle states. No change to audit exports.
Constraints: Existing CSV columns must remain backward compatible.

Acceptance Signal: Contract test proves inactive closed accounts are excluded from standard export and retained in audit export.

Traceability:
- Requirement: Preserve CSV schema -> contract test.
- Requirement: Exclude closed accounts -> integration test with mixed account states.

Graph / Memory / Execution Validation:
- Repository evidence: export query and contract documentation inspected; no migration path in scope.
- Graph evidence: export query, export summary count, and contract docs are affected; audit export remains explicitly excluded.
- Memory evidence: prior audit-export exception accepted only for audit mode; not accepted for standard exports.
- Execution evidence: contract test and mixed-state integration test required before handoff.

Brief To Downstream Map:
- CSV compatibility -> data/API contract owner -> contract test evidence.
- Closed-account exclusion -> backend/data owner -> integration test evidence.
- Audit export exclusion -> non-goal not-present check.

Evidence Limits:
- No production data profile inspected.
- No performance claim authorized by this brief.
```
