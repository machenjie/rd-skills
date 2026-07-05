# Review Rubric

## Passing Standard

The solution must prove the bug was treated as a pattern, not a single line. A
reviewer should see the searched signature, the scope, other occurrences, the
decision for each occurrence, and tests that protect the public behavior.

## Scoring

- 30 percent same-pattern scan completeness.
- 25 percent correctness and minimality of covered fixes.
- 20 percent regression test quality at public behavior boundaries.
- 15 percent impact-scope and residual-risk clarity.
- 10 percent implementation structure and maintainability.

## Automatic Failure Conditions

- No same-pattern scan record before the local fix.
- Fix hides authorization failures or data corruption behind a broad catch-all.
- Matched sibling occurrence is ignored without rationale.
- Final completion lacks validation output.

## Reviewer Notes

Strong answers search by symbol and call shape, not just the exact error text.
They avoid speculative broad refactors and keep the fix aligned with the user
profile ownership model.