# Topology Evidence Freshness

Load this reference when an event-driven architecture decision depends on repository graph, project memory, generated contracts, execution logs, previous incident notes, or prior validation. Treat those inputs as selectors until they are checked against current source after the final topology edit.

## Freshness Record

Record these fields before approving an event flow:

- `current_topology_boundary`: producers, consumers, topics/channels, schemas, registry/config, outbox/relay, generated contracts, tests, dashboards, alerts, runbooks, docs, and deployment wiring inspected after the final edit.
- `graph_claims`: producer-consumer edges, topic bindings, consumer groups, generated artifacts, or dependency paths accepted, rejected, or unknown; include command or report path.
- `memory_claims`: prior topology, incident, migration, owner, SLA, or product consistency note accepted or rejected; include source/date when available.
- `execution_claims`: tests, contract checks, replay drills, DLQ checks, lag/backpressure simulations, dashboard checks, logs, traces, or benchmarks used; include command, exit code, and report path.
- `stale_evidence`: any scan, generated contract, runbook, dashboard screenshot, benchmark, validator, or memory note that predates a producer, consumer, topic, schema, partition key, DLQ, replay, observability, or rollout edit.
- `closure_decision`: approved, blocked, or approved only for inspected boundary, with unknown consumers, untested replay/lag scale, rollback note, and residual owner.

## Reconciliation Rules

- A topology graph before a consumer registration, topic binding, schema change, partition-key change, generated contract update, or outbox relay edit cannot prove final architecture safety.
- Project memory without source/date can suggest a flow candidate, but it cannot approve current consumers, product consistency, or operational ownership.
- A dashboard or alert check that predates metric name, label, topic, consumer group, or runbook changes cannot prove release readiness.
- A replay or lag drill proves only the consumers, fixtures, broker configuration, and load level it exercised; name untested production scale and partition skew.
- Validation must be fresh after the final event architecture edit before handoff claims readiness.
