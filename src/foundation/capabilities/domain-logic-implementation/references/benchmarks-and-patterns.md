# Domain Rule Authority Decisions

These patterns compare rule authority, lifecycle, calculation, cross-boundary consistency, concurrency defense, evolution, and bypass decisions.

## Authority And Failure Matrix

| Rule pressure | Authority test | Failure to expose |
| --- | --- | --- |
| Invariant within one lifecycle | boundary that has the required facts and can reject mutation for reachable writers | caller precheck or public mutation bypasses the guard |
| Value validity and equality | construction boundary when an invalid or ambiguous value cannot safely circulate | partially valid primitive reaches later logic |
| Lifecycle transition | state owner with explicit source, target, actor/policy inputs, denial, and terminal behavior | admin, import, job, or consumer mutates status directly |
| Calculation or derivation | named semantic owner with basis, version, unit, precision, time, and edge behavior | copied formula drifts across reporting or contracts |
| Multi-object policy | boundary that owns the decision inputs and reasons without infrastructure effects | procedural policy object becomes an orchestration dump |
| Cross-boundary invariant | application or consistency handoff when no local owner can enforce the combined fact | an aggregate label promises atomicity the system lacks |
| Storage or concurrency race | readable domain rule plus selected constraint, version, lock, or operation identity | sequential proof passes while competing writes violate the rule |

## Evolution And Bypass Questions

- Which reachable writers, generated paths, support tools, migrations, fixtures, or direct storage operations can avoid the selected authority?
- Which existing values and in-flight commands were valid under an earlier rule version, and how are they read, migrated, rejected, or grandfathered?
- Which projections, public contracts, events, reports, and external consumers copy or interpret the changed calculation or state?
- Which denial, conflict, unknown, or recovery outcome crosses into the application or public failure contract?

## Ownership Boundary

Route use-case sequencing to `service-business-logic`, storage constraints and mapping to `repository-persistence`, model translation to `model-boundary-mapping`, lifecycle discovery to `state-machine-modeling`, and cross-boundary effects to `data-side-effect-flow-tracing`.
