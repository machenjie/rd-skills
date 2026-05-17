# Example Output

```markdown
## Clarification Decision

Proceed decision: Block coding except for read-only investigation.

## Known Facts

- Current export includes inactive accounts.
- The requested change asks to exclude accounts closed before the selected reporting period.

## Blocking Unknowns

- Whether closed accounts must remain visible for regulated audit exports.
- Whether downstream finance reconciliation expects the current row count.

## Non-Blocking Unknowns

- Final label text for the filter can be decided after behavior is approved.

## Assumptions

- Explicit: Product owner expects account status to be evaluated at export time.
- Safe: Existing export permissions remain unchanged because no new resource is introduced.

## Required Owner Response

- Compliance owner must confirm audit visibility requirements.
- Finance owner must confirm reconciliation compatibility.
```
