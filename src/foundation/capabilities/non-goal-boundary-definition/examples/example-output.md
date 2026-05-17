# Example Output

```markdown
## Scope Boundary

In scope:
- Exclude closed accounts from standard monthly export.
- Preserve existing CSV column names and order.

Out of scope:
- Redesign account lifecycle states.
- Add export scheduling.
- Change audit-mode export behavior.

Version boundary:
- This release changes eligibility filtering only.
- Later reporting redesign must not be assumed by current schema or API.

Forbidden assumptions:
- Do not assume all closed accounts are safe to hide from audit workflows.
- Do not add speculative columns for future reporting.

Anti-scope-creep checks:
- Diff review confirms no account lifecycle model changes.
- Contract test confirms CSV schema is unchanged.
```
