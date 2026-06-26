---
name: event-driven-architecture
description: Designs event-driven flows with idempotency, ordering, retry, dead-letter, replay, backpressure, observability, and consistency rules.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "22"
changeforge_version: 0.1.0
---

# Mission

Design event-driven flows that remain **correct, observable, and operationally recoverable** under every adverse delivery condition: duplicate messages, delayed messages, out-of-order messages, replayed messages, poison messages, consumer failures, backpressure, and broker outages — so that eventual consistency is a deliberate product decision with explicit failure semantics, not an optimistic engineering shortcut.

# When To Use

Use this capability when a change: introduces pub-sub, stream processing, or message-queue consumers; adds new event producers that fan out to multiple consumers; designs projections, read models, or CQRS query-side updates driven by events; implements workflow choreography or saga patterns; adds webhooks, change-data-capture (CDC) flows, or external integration events; introduces eventual consistency between two bounded contexts; or changes delivery guarantees, consumer group topology, or partition strategy on existing flows.

# Do Not Use When

Do not convert a synchronous dependency to asynchronous without a clear reason: user-visible latency reduction, fault isolation from downstream failure, throughput decoupling, or explicit eventual consistency acceptance by the product. Asynchrony that is added for convenience without these reasons introduces operational complexity with no return. Do not use this capability for in-process event bus (e.g., Spring ApplicationEventPublisher scoped to a single service transaction) — that is a domain-event modeling concern, not an architecture concern.

# Stage Fit

Use during architecture planning when a change introduces cross-bounded-context events, asynchronous fan-out, choreography, projection rebuild, CDC, webhook-to-event flow, or product-visible eventual consistency. Use during implementation review when producers, consumers, outbox/relay, partition keys, schema evolution, replay, DLQ ownership, lag/backpressure, or event observability change. Use during testing when duplicate delivery, out-of-order arrival, poison message routing, replay safety, lag alerting, and stale projection behavior need evidence. Hand off to `domain-event-modeling` for payload semantics, `message-queue-design` for broker mechanics, `transaction-consistency` for outbox/saga invariants, and `reliability-observability-gate` for production SLO readiness.

# Non-Negotiable Rules

- **Every consumer side effect must be idempotent.** At-least-once delivery (the default for Kafka, RabbitMQ, SQS, Pulsar) guarantees duplicates. Every operation a consumer performs — database write, external API call, email send, ledger debit — must be safe to execute more than once. Idempotency key strategy must be defined per consumer.
- **Ordering guarantees must be declared, not assumed.** Kafka guarantees ordering within a partition (not across partitions). RabbitMQ classic queues do not guarantee ordering under parallel consumers. FIFO queues (SQS FIFO, RocketMQ) guarantee ordering within a message group. If consumers require per-aggregate ordering, the partition key (Kafka) or message group ID (SQS FIFO) must equal the aggregate ID.
- **Dead-letter queues are mandatory.** Every consumer must define a DLQ (dead-letter queue or dead-letter topic). A message that fails maximum retries must be routed to the DLQ, not discarded. DLQ events must generate an alert when depth exceeds threshold. DLQ ownership, inspection tooling, and replay procedure must be assigned to a named team.
- **Replay must not repeat irreversible side effects.** Event replay is a critical operational procedure (projection rebuild, incident recovery). Before enabling replay: identify all consumers that perform irreversible operations (payment capture, email send, webhook fire, ledger entry). Mark those operations as deduplication-gated: replay only if idempotency key has not been processed.
- **Backpressure is defined, not hoped for.** Producers must not outpace consumer processing capacity indefinitely. Define: consumer lag threshold (e.g., > 10,000 messages = alert), lag growth rate threshold, consumer scaling trigger (KEDA, Kubernetes HPA based on Kafka consumer lag), and circuit-breaker behavior when lag is critical.
- **Schema evolution follows compatibility contracts.** Event schemas consumed by multiple consumers cannot be changed without compatibility analysis. Backward-compatible changes (add optional field) require only a schema version bump. Breaking changes (remove field, rename, type change) require a new topic/channel and a migration period with dual-publishing.
- **Observability is not optional.** Every event flow must emit: event throughput (events/second per topic/partition), consumer processing rate, consumer lag, DLQ depth, error rate per consumer group, and end-to-end event latency (from produce time to consumer commit time). Without these signals, operational diagnosis is guesswork.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| New event flow | New producer, consumer, topic, stream, projection, CDC flow, webhook bridge, or async fan-out. | Decide whether async is justified and define source-of-truth, flow topology, delivery semantics, consistency window, and owners. | Sync alternative rejected, producer/consumer map, event contract owner, transaction boundary, stale-read product decision. | `architecture-impact-reviewer`, `domain-event-modeling`, `message-queue-design` | Broker tuning before architecture fit. |
| Existing flow evolution | Producer/consumer, schema, partition key, consumer group, DLQ, replay, or lag behavior changes. | Preserve old consumers and operational recovery while evolving the flow. | Consumer inventory, compatibility class, old/new schema behavior, replay impact, rollback/cutover plan. | `version-compatibility`, `contract-testing`, `quality-test-gate` | Breaking schema edit in-place. |
| Consistency and side-effect design | DB write plus event publish, saga choreography, external side effect, projection rebuild, or outbox/relay path. | Prevent dual-write loss, ghost events, irreversible replay effects, and partial saga state. | Outbox/commit boundary, side-effect order, idempotency key, compensation/reconciliation path, non-replayable consumers. | `transaction-consistency`, `idempotency-retry-design`, `data-side-effect-flow-tracing` | Event-before-commit publish. |
| Operational readiness | Consumer lag, DLQ depth, poison messages, replay drills, backpressure, autoscaling, or incident recovery. | Make event behavior observable, alertable, replayable, and bounded under failure. | Lag/DLQ metrics, alert owner, replay runbook, backpressure threshold, recovery validation. | `reliability-observability-gate`, `observability`, `degradation-circuit-breaking` | Metrics without owner/runbook. |
| Sensitive or regulated eventing | Events include PII, financial, authorization, audit, ledger, notification, or compliance-relevant data. | Minimize payload, restrict consumers, protect audit integrity, and prove duplicate/replay safety. | Data classification, allowed consumers, privacy decision, audit retention, duplicate/replay tests. | `security-privacy-gate`, `permission-boundary-modeling`, `quality-test-gate` | Payload fan-out with sensitive data. |

# Industry Benchmarks

Anchor against Kafka/Pulsar/Pub/Sub/SQS/RabbitMQ delivery semantics, CloudEvents and AsyncAPI event contracts, transactional outbox and inbox patterns, CQRS projections, saga choreography/orchestration, CDC/Debezium, schema registry compatibility, KEDA lag-based autoscaling, and OpenTelemetry trace propagation. Keep this body focused on routing, evidence, output, and quality gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for delivery guarantees, saga selection, lag/backpressure patterns, replay-safety classification, outbox/inbox flow, and operational anti-patterns.

# Selection Rules

Select this capability when **asynchronous multi-service event flow design** is primary. Adjacent routing:

- Prefer `domain-event-modeling` when event payload semantics, producer/consumer contracts, and event naming are primary.
- Prefer `message-queue-design` when broker infrastructure selection, queue topology, consumer group configuration, and binding design are primary.
- Prefer `async-job-design` when the concern is background job execution (workers, queues, cron) rather than domain fact communication.
- Prefer `transaction-consistency` when distributed transaction coordination and saga compensation logic are the main concern.
- Prefer `reliability-observability-gate` for production SLO/SLA review of event-driven flows.

# Risk Escalation Rules

Escalate when: event loss, duplication, or replay would cause a financial debit, customer notification, or inventory change to happen twice; an out-of-order event would corrupt a state machine (e.g., `OrderCancelled` before `OrderPlaced`); consumer lag is growing in production and no auto-scaling policy is defined; a schema change would break active consumers with no migration window; a DLQ has been accumulating events for > 1 hour with no acknowledged owner; a saga has no compensation events defined for any failure path.

# Proactive Professional Triggers

- **Signal:** async flow is proposed mainly to "decouple" services, avoid waiting for a dependency, or replace a simple synchronous call. **Hidden risk:** temporal coupling and eventual consistency are introduced without product acceptance or operational recovery. **Required professional action:** compare synchronous call, local module, outbox event, queue command, and choreography alternatives before approval. **Route to:** `architecture-impact-reviewer`, `architecture-tradeoff-analysis`. **Evidence required:** rejected synchronous alternative, product consistency decision, owner map, and failure blast radius.
- **Signal:** producer writes state and publishes an event in separate steps or from mapper/domain code. **Hidden risk:** lost events, ghost events, and hidden side effects. **Required professional action:** define transactional outbox, publish-after-commit, CDC, or explicit safe exception. **Route to:** `transaction-consistency`, `data-side-effect-flow-tracing`. **Evidence required:** transaction boundary, outbox/relay owner, idempotent relay behavior, and partial-failure test or review artifact.
- **Signal:** consumer performs irreversible side effects such as payment capture, email/SMS, webhook POST, ledger entry, entitlement grant, or inventory mutation. **Hidden risk:** duplicate delivery or replay repeats the side effect. **Required professional action:** classify replay safety and require durable dedupe before enabling retry or replay. **Route to:** `idempotency-retry-design`, `quality-test-gate`, `security-privacy-gate` when sensitive. **Evidence required:** idempotency key scope, dedupe store, replay procedure, duplicate/replay validation, residual risk owner.
- **Signal:** event schema changes or a new consumer is added without consumer inventory, schema compatibility mode, generated contract check, or migration window. **Hidden risk:** active consumers deserialize wrong data or silently corrupt calculations. **Required professional action:** run consumer impact and compatibility review before changing the event contract. **Route to:** `domain-event-modeling`, `version-compatibility`, `contract-testing`. **Evidence required:** consumer inventory, old/new schema diff, compatibility result, rollout/rollback plan.
- **Signal:** consumer lag, DLQ depth, poison messages, replay, or backpressure is described but no alert owner, runbook, or recovery drill is named. **Hidden risk:** event system appears healthy while work is delayed or lost. **Required professional action:** require operational readiness evidence before handoff. **Route to:** `reliability-observability-gate`, `observability`, `degradation-circuit-breaking`. **Evidence required:** lag/DLQ metrics, thresholds, dashboard/runbook owner, replay drill or not-verified disclosure.
- **Signal:** prior project memory or repository graph suggests event topology, but current producers, consumers, schemas, topics, or generated artifacts were not inspected. **Hidden risk:** stale topology misses hidden consumers or retired flows. **Required professional action:** confirm memory/graph with current source and generated contracts. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected memory, freshness limit, unknown consumers.

# Critical Details

Event-driven systems trade synchronous coupling for temporal complexity. Precision failures:

- **"Fire and forget" without DLQ.** A producer publishes an event; the consumer fails; there is no DLQ; the event is lost. This is not eventual consistency — this is data loss. DLQ is not optional infrastructure.
- **Replay re-fires payment.** A replay job rebuilds a projection by re-processing all events from the beginning. The `PaymentCaptured` event passes through a consumer that calls Stripe Capture API again. The customer is charged twice. Every replay procedure must audit which consumers perform non-idempotent external operations and gate them behind deduplication.
- **Partition-key mistake.** A Kafka producer uses `customerId` as partition key. Two events for the same `orderId` but different `customerId` (e.g., a reassigned order) land on different partitions. The consumer processes `OrderShipped` before `OrderCreated`. State machine transitions to invalid state.
- **Exactly-once illusion.** Kafka EOS (exactly-once semantics) guarantees exactly-once delivery within Kafka. It does NOT guarantee exactly-once execution of external side effects (database writes, HTTP calls). Application-level idempotency is still required for any consumer that touches an external system.
- **Consumer group over-parallelism.** A consumer group has 20 parallel consumers on a topic with 6 partitions. 14 consumers are idle (Kafka assigns max 1 consumer per partition per consumer group). Partition count drives maximum parallelism; scale consumers to match partition count.
- **Stale projection read with no disclosure.** A user creates an order; the projection updates 500ms later; the user is redirected to an order list page that reads the stale projection; their new order is not visible. The product must decide: (1) use read-your-writes consistency for this flow; (2) show a "refreshing" state; or (3) use synchronous read from the command side. "It'll catch up soon" is not a product decision.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| Consumer performs `INSERT` without idempotency key | Replay or duplicate delivery creates duplicate records |
| DLQ defined but no alert on DLQ depth | Failures accumulate silently for days; data loss discovered late |
| Kafka partition key = `Math.random()` | No ordering guarantee for any aggregate; state machine corruption |
| Saga with no compensation events | Business transaction permanently stuck on partial failure; no rollback path |
| `acks=0` Kafka producer (fire and forget) | Events lost on broker failure; no durability |
| Consumer lag not monitored | Production lag grows to 2M messages; service appears healthy; events hours old |
| Schema field removed without consumer registry check | Active consumer deserializes null; calculation fails silently |
| Exactly-once Kafka claimed = no idempotency needed | External DB write still duplicated; Kafka EOS only covers broker-side |

# Failure Modes

- Consumer duplicate delivery creates two payment charges; customer charged twice; refund required; SLA breach.
- DLQ accumulates 50,000 messages over 48 hours; no alert; orders in permanent "processing" state; mass customer escalation.
- Partition key assigned to random UUID; `OrderCancelled` arrives before `OrderCreated`; state machine error; order stuck.
- Replay rebuilds read model; payment capture consumer re-fires; 10,000 duplicate charges; production incident P0.
- Consumer lag reaches 500,000 messages; auto-scaling not configured; service processes events 3 hours old; financial totals stale; compliance SLA violated.
- Saga no compensation path: inventory reserved, payment fails, no `ReleaseInventory` compensation event defined; inventory permanently locked.
- Schema field renamed: `price` → `unitPrice`; consumers read null; order total = $0.00; passed validation; financial loss.
- `acks=0` on critical payment event topic; broker restart during peak; 200 events lost; payment status unknown.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 selection, boundary, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete event-flow plan, adding a producer or consumer, changing delivery/order/retry/DLQ/replay behavior, or accepting eventual consistency. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when delivery guarantee comparison, saga pattern choice, lag/backpressure thresholds, replay-safety classification, outbox/inbox design, or operational anti-pattern detail is needed. Use [examples/example-output.md](examples/example-output.md) only when the expected plan shape is unclear. Do not load references for pure routing or metadata-only edits with no event topology, schema, or recovery behavior change.

# Output Contract

Return an event architecture plan with:

- `mode_selected` (new event flow, existing flow evolution, consistency/side-effect design, operational readiness, sensitive/regulated eventing)
- `boundaries_inspected` (producers, consumers, topics/channels, schemas, registry/config, outbox/relay, generated contracts, tests, dashboards, runbooks, and prior memory accepted or rejected)
- `source_evidence` (current-source observations that prove the topology, not inferred architecture memory)
- `producers` (service, event name, emission trigger, transaction boundary, outbox mechanism)
- `consumers` (service, event name, processing logic, idempotency key, DLQ destination, owner)
- `event_schemas` (CloudEvents-compatible; schema version; registry location; compatibility mode)
- `delivery_guarantee` (at-least-once / exactly-once per consumer; broker and config)
- `ordering_requirement` (per-aggregate / per-partition / none guaranteed; partition key strategy)
- `retry_policy` (max retries, backoff algorithm, retry delay, DLQ threshold)
- `dlq_policy` (topic name, alert threshold, owner team, replay procedure, runbook)
- `replay_safety` (per-consumer classification; deduplication gate for non-idempotent operations)
- `consistency_model` (eventual; read-your-writes exception; stale read disclosure strategy)
- `backpressure_behavior` (lag threshold, auto-scaling config, circuit-breaker, load-shedding)
- `saga_design` (if applicable: steps, compensation events, orchestrator/choreography, timeout)
- `observability` (metrics: throughput, lag, DLQ depth, error rate, end-to-end latency)
- `schema_evolution_plan` (compatibility matrix; breaking change migration procedure)
- `tests` (idempotency test, out-of-order test, DLQ routing test, replay dedup test, lag alarm test)
- `changed_flow_to_validation_map` (each producer, consumer, schema, partition key, retry/DLQ policy, replay path, or observability change mapped to validation)
- `reuse_and_placement_rationale` (existing event/broker/reference reused, rejected alternatives, and why no speculative queue/service abstraction was added)
- `behavior_preservation` (old producers, old consumers, old schemas, old replay procedure, old dashboards, and old runbooks that remain valid)
- `validation_evidence` (commands, reports, fixtures, contract checks, replay drills, dashboard/alert checks, or not-verified disclosure)
- `handoff_boundaries` (which decisions move to domain event, queue design, transaction consistency, idempotency, security, reliability, or release gates)
- `evidence_limits` (what was not inspected, unknown consumers, untested replay/lag scale, and residual risk owner)

# Evidence Contract

Close an event-driven architecture plan only when these answers are concrete:

- **Current topology inspected:** name the producer paths, consumer paths, event schemas, topic/channel config, outbox/relay, generated artifacts, tests, dashboards, runbooks, docs, and prior memory that were checked. If no implementation exists, say so explicitly.
- **Async justification:** state the concrete reason async is preferred over synchronous call, local module, or simpler queue/job design, plus the product-visible eventual-consistency decision.
- **Consistency and side-effect proof:** identify the commit point, outbox/inbox or CDC mechanism, consumer idempotency boundary, replay-safe and replay-unsafe consumers, and compensation/reconciliation path.
- **Compatibility proof:** state how old producers, old consumers, schema registry compatibility, generated clients/contracts, and replay/backfill procedures behave after the change.
- **Operational proof:** name lag, DLQ, error, throughput, replay, and end-to-end latency signals, plus alert/runbook owner or explicit not-verified residual risk.
- **Validation result:** include command names and pass/fail status. Do not claim event architecture readiness from design reasoning alone.
- **What evidence does not prove:** call out untested broker outage, partition skew, large replay, high-cardinality metrics, unknown consumers, privacy fan-out, or production lag assumptions.
- **Next gate:** name the next capability or human review required when queue mechanics, event payloads, transaction consistency, privacy, reliability, or release readiness is outside this capability.

# Quality Gate

The architecture design is complete only when:

1. Every consumer side effect is classified as idempotent or has a documented idempotency mechanism.
2. Ordering guarantees declared per-consumer; partition key strategy specified where ordering required.
3. DLQ defined for every consumer; alert threshold, owner, and replay procedure assigned.
4. Replay safety classification completed per consumer; non-idempotent operations gated by deduplication.
5. Schema compatibility mode declared in registry; breaking change migration procedure documented.
6. Consumer lag thresholds defined; auto-scaling trigger configured; backpressure strategy documented.
7. All saga failure paths have compensation events defined; orchestrator or choreography pattern chosen.
8. Observability metrics listed: throughput, lag, DLQ depth, error rate, end-to-end latency.
9. Eventual consistency impact on product UX documented (stale read disclosure or read-your-writes exception).
10. Tests cover: duplicate delivery, out-of-order, DLQ routing, replay deduplication, consumer group lag.

# Used By

- architecture-impact-reviewer
- integration-change-builder
- data-middleware-change-builder

# Handoff

Hand off to `domain-event-modeling` for event payload and schema design; `message-queue-design` for broker topology and infrastructure; `transaction-consistency` for saga compensation and distributed rollback; `reliability-observability-gate` for production SLO review; `data-migration-design` for projection rebuilds during event schema migrations.

# Completion Criteria

The capability is complete when **asynchronous flow correctness is explicit across idempotency, ordering, retries, DLQ ownership, replay safety, backpressure, schema evolution, and observability** — with no optimistic "it'll be fine" assumptions about delivery guarantees, no DLQ without an owner, and no eventual consistency without a product-acknowledged disclosure strategy.
