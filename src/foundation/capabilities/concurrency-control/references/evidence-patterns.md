# Concurrency Control Evidence Patterns

Use this reference when concurrency closure depends on parallel proof, lock/lease artifacts, graph-memory freshness, or changed-concurrency-to-validation mapping.

## Evidence Map
- **Shared-resource invariant:** prove resource, actors, invariant, overlap scenario, mechanism, rejected alternatives, concurrent test command, artifact, exit code, and residual interleaving risk.
- **Duplicate effect prevention:** prove idempotency key scope, unique storage, payload fingerprint, replay/conflict behavior, duplicate test, and retention owner.
- **Worker parallelism or ordering:** prove partition/claim strategy, idempotent handler, bounded pool, queue depth/lag evidence, redelivery test, and DLQ or terminal state.
- **Distributed lease or leader:** prove provider guarantee, TTL/release, fencing token source, stale-token rejection test, timeout behavior, and advisory-only residual risk when applicable.
- **Contention or deadlock repair:** prove reproducer, lock-wait or hot-row report, canonical lock order, before/after stress/profile result, same-pattern scan, and watch signal.

## Evidence Rules
- Every accepted concurrency item names command or validator, output/report artifact, exit code, freshness, what it proves, what it does not prove, and next gate.
- Serial-only tests, stale memory, repository graph proximity, or plausible lock choice do not prove overlap safety without current source and concurrent, stress, race-detector, or redelivery evidence.
