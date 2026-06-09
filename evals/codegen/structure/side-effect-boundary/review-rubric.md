# Review Rubric

## Passing Standard

The solution passes when pure policy decisions are isolated, side effects are coordinated at explicit boundaries, return contracts are structured, and tests verify both decision and orchestration behavior.

## Scoring

- 30 percent side-effect separation: policy is pure and infrastructure stays in adapters or orchestration.
- 25 percent signature and result structure: no boolean/null ambiguity for complex outcomes.
- 20 percent clarity: main flow is readable and side effects are named.
- 20 percent tests: pure decision tests and public orchestration tests cover failure paths.
- 5 percent refactor safety: old behavior preservation evidence is present.

## Automatic Failure Conditions

- Policy writes database, calls payment API, emits events, or mutates cache.
- Side effects are hidden in helpers named `utils`, `helper`, or `common`.
- Tests assert only mock calls to private functions.
- Result contract does not expose denial or retry semantics.

## Reviewer Notes

Look for a simple service/use-case orchestration path and a pure decision object or function with domain names. Penalize unnecessary abstractions that make the side-effect boundary harder to see.
