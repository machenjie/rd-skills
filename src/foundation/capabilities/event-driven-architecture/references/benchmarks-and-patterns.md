# Event-Driven Architecture Benchmarks And Patterns

Load this reference when delivery, ordering, replay, consistency, backpressure, schema or workflow ownership changes an event architecture. Broker features never prove external side effects occur exactly once.

## Delivery And Ordering Contract

| Axis | Required decision | Failure/proof |
| --- | --- | --- |
| Event fact/owner | Name immutable fact, producer authority, consumers and retention purpose. | Command-like vague events or multiple producers create ambiguous truth. |
| Delivery | Choose at-most/at-least/effectively-once behavior from loss/duplicate risk. | At-least-once requires durable consumer idempotency; broker transactions stop at their boundary. |
| Ordering | Define ordering scope and partition/routing key only where business behavior depends on it. | Global-order assumptions, key skew and cross-partition races need explicit handling. |
| Ack/offset | Commit only after durable effect/status or owned inbox state. | Early ack loses work; effect-before-ack without dedupe duplicates it. |
| Failure/DLQ | Classify retryable, poison, permanent and unknown outcomes; name quarantine/replay owner. | An unalerted DLQ or infinite hot retry hides product failure. |
| Backpressure/lag | Treat queue age/lag as product freshness with admission, pause, scale or degradation action. | Depth alone lacks arrival/service-rate context and recovery plan. |

## Consistency, Workflow, And Replay

- Use outbox when source state and event publication must agree.
- Use inbox or conditional writes for consumer deduplication.
- For each distinct dual-write order, scan missing-event and phantom-event recovery paths.
- Saga orchestration fits one visible workflow owner; choreography requires mature event ownership and stuck-workflow detection. Compensation must itself be ordered, idempotent, observable and recoverable when it fails.
- Replay classifies each effect as safe, deduplicated, reconcilable, compensated, suppressed, or manually approved. Rate-limit by tenant/resource and preserve original causation/version.
- CDC is a transport from database log, not domain-event semantics. Map row changes to owned contracts, handle snapshot/live ordering, schema evolution, deletes and cutover reconciliation.

## Schema And Consumer Compatibility

| Change | Required evidence |
| --- | --- |
| Field/type/default/enum change | Registry/schema compatibility in the producer→consumer direction, old/new fixtures and unknown handling. |
| Event rename/removal | Consumer inventory, dual publish/version/bridge, replay window and usage evidence before cleanup. |
| New consumer | Start position, historical replay behavior, idempotency, permission/data classification and capacity impact. |
| Rolling deploy | Old producer/new consumer and new producer/old consumer paths plus generated artifacts where applicable. |

## Operability, Limits, And Routing

- Bound telemetry labels and expose publish/consume rate, age/lag, retries, duplicates/conflicts, failure/DLQ class, processing duration and replay progress only for the changed path; map signals to an owner/runbook action.
- Inspect current producers, schemas, brokers/config, consumers, offsets/inboxes, effects, tests and runbooks. Static source cannot prove hidden consumers, broker/provider guarantees, production ordering, irreversible replay or recovery capacity.
- Route fact semantics to `domain-event-modeling`, commit order to `transaction-consistency`, idempotency to `idempotency-retry-design`, broker topology to `message-queue-design`, consumers to `consumer-impact-analysis`, signals to `observability`, and public schema change to `data-api-contract-changer`.

Reject database rows published as unowned domain facts, broker-EOS claims for external effects, unkeyed ordering assumptions, and dual writes without recovery. Also reject ownerless choreography, consumer-blind schema changes, uncontrolled replay of irreversible effects, and lag dashboards without a product threshold or action owner.
