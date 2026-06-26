# Validation Freshness Handoff

Use this reference when repository context must feed validation selection, review scope, rollback notes, or final handoff.

## Handoff Fields

| Field | Required Evidence | Limit |
| --- | --- | --- |
| Changed path | Source, registry, docs, tests, reports, generated output, or build artifact. | Unchanged but dependent paths may still need review. |
| Validator candidate | Narrow, module, full, build, install, docs, report, or eval command. | Candidate is not proof until executed and parsed. |
| Covered scope | Paths, behavior, generated outputs, or registry links exercised. | Partial scope must remain partial in closure. |
| Freshness status | Current, stale, partial, failed, not run, not verified, or unsupported. | Any later material edit invalidates earlier proof for that path. |
| Review scope | Owner capability, reviewer capability, repaired files, and re-review status. | Owner self-review is not enough for closure. |
| Residual risk | Unknown owner, omitted edge, unrun validator, unsupported graph, or stale report. | Residual risk needs next owner and next gate. |

## Closure Rules

1. Validation evidence must run after the final material edit or be marked stale.
2. A targeted command proves only its covered paths, not full release readiness.
3. Report, dist, package, and install outputs need source/build freshness before handoff.
4. Handoff must include rollback clue, validation limit, residual risk, and next owner.
