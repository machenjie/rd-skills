# Data Migration Design Benchmarks And Patterns

Use when migration phase, cutover, or recovery alternatives remain open after engine, volume, locks, topology, and consumers are known.

## Option Comparison

| Decision | Compare | Reject or escalate when |
|---|---|---|
| Transition | additive; staged permissive shape, backfill, validation, enforcement; bridge before rename or removal | one-step rewrite or drop breaks mixed versions, locks data, or destroys rollback state |
| Live data | owned checkpointed idempotent batches; CDC or dual path; pause, throttle, retain source, or reverse cutover | writers, identity, ordering, capacity, tenant completeness, or deletion authority is unknown |
| Phase | expand, migrate, contract, and cleanup selected from observed skew and consumer control | a fixed phase count lacks compatibility and exit evidence |
| Recovery | additive or code rollback, compensation, forward repair, or rehearsed restore at an owned point of no return | tier transition, owner, integrity, dependencies, or recovery objective is unproved |

For a replayable migration batch, use an explicit predicate or version marker so reruns update rows that still require migration. Define how concurrent writers merge or dual-write. This replay proof does not establish production lock, lag, or capacity safety.

Record selected and rejected approaches with current evidence and limits. Return unresolved model, contract, consumer, atomicity, release, recovery, observability, or regulated-data gaps to Main; do not self-reroute.

Reject unguarded reruns, direct live-contract renames, unbounded mutation, pre-inspection checksum repair, unproved cleanup, unreconciled CDC, ignored generated consumers, or recovery claims without proof.
