# Event Evidence Freshness

Load this reference when a domain event decision depends on repository graph, project memory, generated contracts, execution logs, prior validation, or migration history. These sources are selectors until reconciled with current source after the final event edit.

## Freshness Record

Record these fields before approving an event catalog:

- `current_source_boundary`: producer, aggregate transition, schema, registry/config, outbox/relay, consumers, tests, generated contracts, runbooks, and docs inspected after the final edit.
- `graph_claims`: producer/consumer topology, topic/channel, generated artifact, or dependency facts accepted, rejected, or unknown; include command or report path.
- `memory_claims`: prior event name, owner, incident, migration, diagram, or architecture note accepted or rejected; include source/date when available.
- `execution_claims`: tests, validators, contract checks, replay fixtures, DLQ checks, logs, traces, or benchmarks used; include command, exit code, and report path.
- `stale_evidence`: any scan, memory, generated contract, fixture, benchmark, or validator that predates a producer, schema, consumer, outbox, DLQ, replay, or privacy edit.
- `closure_decision`: approved, blocked, or approved only for inspected boundary, with residual owner and rollback note.

## Reconciliation Rules

- A graph scan before a consumer registration, topic binding, schema file, generated contract, or outbox relay edit cannot prove the final topology.
- Project memory without source/date can suggest an event candidate, but it cannot approve fact semantics, consumers, or compatibility.
- A generated contract check is stale when schema, registry mode, event type, package namespace, or consumer code changes afterward.
- A replay or DLQ test proves only the consumers, fixtures, and broker behavior it exercised; name untested production lag, large replay, and unknown consumers.
- A validation pass must be fresh after the final event modeling change before handoff claims readiness.
