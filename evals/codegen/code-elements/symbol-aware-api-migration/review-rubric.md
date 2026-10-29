# Review Rubric

## Passing Standard

Migrate the declared symbol and preserve its observable contract. Return unresolved references without partial changes when identity or call semantics cannot be proved.

## Scoring

Assess symbol identity, atomic changes, preserved semantics, UTF-8 spans, residual imports, and idempotence through executable assertions.

## Automatic Failure Conditions

Rewriting an unrelated `fetch` symbol fails. Accepting compilation alone, hiding unresolved references, or changing explicit caller policies also fails.

## Reviewer Notes

This is a flat-module fictional API fixture. It does not prove general Python resolution, vendor migration rules, type-checker correctness, or production rollout safety.
