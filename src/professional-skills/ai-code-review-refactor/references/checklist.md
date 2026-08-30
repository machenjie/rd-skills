# AI Review Checklist

- Verify reachable failure mechanisms.
- Verify imports, APIs, methods, config keys, and generated file paths exist.
- Compare patterns against nearby code.
- Identify hidden assumptions and invented contracts.
- Report each reachable issue with source evidence, impact, and an outcome-based correction direction.
- Keep review mode non-mutating and leave implementation choices to the owning task agent.
- Treat clone mechanisms as candidates until task-specific semantic-equivalence tests cover the accepted value domain and runtime boundary; otherwise report the evidence gap.
- Review type safety, null handling, and error handling.
- Check dependency additions and package scripts.
- Confirm generated tests exercise real behavior.
- Report the safe correction boundary, rollback constraints, and unverified behavior.
- Record findings by severity with file and line evidence.

## Professional Decision Rules

- Judge every changed path in the actual latest diff within the fixed boundary.
- Apply the assigned review-risk boundary, severity, evidence, repair, and re-review rules without mutation, scope expansion, or inferred approval.

## High-Value Gotchas

- A summary or self-review is not an independent review of the actual diff.

## Execution Checklist

1. Inspect the actual diff, affected contracts, tests, and fixed review-risk selection.
2. Return reachable findings or an explicit no-finding result with proof limits.
