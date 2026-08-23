# Transaction Consistency Evidence Patterns

Use this map for a named transaction, isolation, effect-ordering, conflict, or recovery proof. Non-triggered paths remain proof limits.

## Consistency Claim-To-Evidence Map

| Claim | Current evidence | Proof limit |
| --- | --- | --- |
| Local atomicity | Writers, invariant, touched state, effective transaction, rollback case, and invariant test. | Inspected path; not hidden writers, replicas, or future migrations. |
| Lost-update control | Colliding writers, conflict mechanism, overlap proof, and caller outcome. | Named writers; not every timeout or production contention profile. |
| Set/range control | Set invariant, datastore/query behavior, selected control, and write-skew or phantom proof. | Inspected query; not every ORM SQL or predicate-lock variant. |
| Remote-effect ordering | Transaction timeline, external protocol, lock/latency evidence, crash window, and recovery proof. | Ordering; not provider availability or exactly-once effects. |
| Outbox/inbox durability | Atomic state-and-intent record, relay evidence, effect identity, duplicate replay, and stuck owner. | Durable intent; not broker order or every downstream effect. |
| Compensation safety | Persisted effect identity and reversal inputs, step-failure proof, retry limit, and terminal owner. | Representative failures; not universal reversibility or success. |
| Reconciliation | Authoritative key, drift classes, freshness bound, idempotent correction, alert, and owner. | Inspected drift; not instant detection or every production distribution. |
| Evidence freshness | Current writer/topology scan, prior-claim comparison, artifact, skipped boundaries, and verdict. | Current graph; later edits and undiscovered entrypoints reopen proof. |

## Freshness And Scope

- Treat prior inspection, evidence, reports, and reviews as selectors until current handlers, repositories, migrations, relays, consumers, adapters, tests, and artifacts confirm the claim.
- Reopen after edits to transaction scope, isolation, lock order, repositories, ORM hooks, migrations, retries, topics, relays, consumers, compensation, fixtures, reports, or commands.
- Record inspected and skipped writers, stores, side effects, recovery, tests, signals, and runbooks; mark accepted unexecuted checks `planned` or `not_run` with reason and owner.

## Tool And Handoff Boundary

- A database, queue, cache, provider, or production probe requires authorized scope, timeout, stop, rollback or reset, and sensitive-value redaction.
- Record commit, acknowledgement, and side-effect order with crash windows, retries, external effects, status, proof limit, residual risk, and owner.
