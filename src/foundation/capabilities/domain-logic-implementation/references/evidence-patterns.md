# Domain Rule Evidence Patterns

These evidence patterns bound claims about domain-rule authority, failure timing, transitions, calculations, cross-boundary ownership, and rule evolution.

## Rule Claim Map

| Domain-rule claim | Current authority evidence | Unproved boundary |
| --- | --- | --- |
| Selected authority owns the rule | source path, accepted inputs, reachable writer scan, rejected placements, and public domain operation | uninspected or future writer paths can bypass the route |
| Invalid state fails before effect | denied-case evidence plus persistence and external-effect call order | separate storage scripts or competing writes need their own defense proof |
| Transition semantics are complete | changed source/target pairs, actor or policy inputs, terminal denial, and typed outcomes | states introduced after the evidence window remain outside the claim |
| Calculation semantics are stable | basis/version, unit, precision, rounding/time rules, boundary cases, and consumer scan | uninspected reports or external copies can retain older semantics |
| Cross-boundary rule is owned | local authority limit plus transaction, idempotency, compensation, or reconciliation handoff | production race windows remain unproved without representative concurrency evidence |
| Rule evolution preserves meaning | historical fixtures, old/new coexistence, migration or grandfathering decision, and replay behavior | production data shapes beyond the fixture scope remain unproved |

## Freshness And Limits

- Refresh after changes to rule inputs, owner, writers, status values, calculation basis, persistence mapping, commands, events, projections, generated artifacts, or tests.
- Separate domain denial proof from persistence-constraint, concurrency, and application-orchestration proof.
- Treat prior incidents and neighboring patterns as risk selectors until current paths and final-edit validation confirm them.
- Close with unsearched writers, historical-data scope, concurrency/environment limits, consumer gaps, residual owner, and specialist handoff.
