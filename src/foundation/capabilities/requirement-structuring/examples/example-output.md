# Example Output

```markdown
## Structured Change Brief

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
```
