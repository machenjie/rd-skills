# Data Side-Effect Flow Tracing Benchmarks And Patterns

Use this reference when `data-side-effect-flow-tracing` needs more depth than the main `SKILL.md` should carry efficiently. Keep the body focused on routing, output, and gates; use this file for side-effect classification, ordering patterns, compensation, nondeterminism, same-pattern scans, and anti-pattern review.

## Benchmark Anchors

- Command-query separation: pure reads and decisions should not mutate external state.
- Transactional outbox and publish-after-commit: consumers should not observe rolled-back state.
- Unit of work and source-of-truth cache discipline: writes, cache, and events need explicit order.
- Idempotent side-effect design: when an operation can be retried or replayed, define duplicate behavior for each reachable effect and record unknown semantics for externally owned effects.
- Saga compensation: multi-step durable effects need forward recovery or explicit irreversible risk.
- OpenTelemetry and audit logging: observability should record behavior without changing business outcome or leaking sensitive data.

## Side-Effect Classification Matrix

| Effect type | Required boundary | Escalate when |
| --- | --- | --- |
| Persistence write | Repository/unit-of-work owner, transaction scope, rollback behavior. | Multiple stores or partial writes are possible. |
| Cache mutation | Source of truth, key dimensions, stale tolerance, invalidation order. | Tenant/permission scope can leak or stale data can harm users. |
| Event or queue publish | Commit point, outbox/pre-commit contract, consumer visibility. | Duplicate, rollback, or replay can trigger irreversible effects. |
| External IO/webhook | Adapter, timeout, retry stance, idempotency, reconciliation. | Provider failure or duplicate delivery affects money/data/permissions. |
| File/storage IO | Writer owner, cleanup, retention, rollback/reconciliation. | DB rollback can orphan objects or expose private data. |
| Nondeterministic read | Clock/random/env/flag boundary, injection, replay/audit impact. | Business logic becomes flaky or non-auditable. |
| Observability | Field list, redaction, exporter failure, no-business-outcome guarantee. | Logs/metrics/traces can mutate state or leak sensitive data. |

## Ordering Pattern

```text
input -> validation -> authorization/policy -> pure mapping -> transaction begin
-> durable write + optional outbox record -> commit -> direct publish or outbox relay -> cache invalidation/refresh
-> external notification/job -> response, compensation, or operator-visible failure
```

Use the actual local order. Deviations are allowed only when the owner states the contract and validation.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| Mapper writes to repository. | Pure-looking code mutates state and evades tests. | Move effect to service/repository/job boundary or document framework exception. |
| Event before commit. | Consumers observe rolled-back state. | Publish after commit or use outbox. |
| Cache invalidated before failed persistence. | Fresh cache hides missing durable state. | Tie cache order to commit and source of truth. |
| Retry repeats non-idempotent write. | Duplicate charge, event, file, or provider action. | Define idempotency key and duplicate response. |
| Logger callback swallows error. | Observability changes business result. | Keep exporter failure non-authoritative. |
| Stale prior evidence proves flow safety. | Current wrappers or generated clients drifted. | Re-read current source, tests, graph, and validation output. |

## Handoff Boundaries

- Use `transaction-consistency` for isolation, atomicity, and commit semantics after the effect path is visible.
- Use `cache-design` for source-of-truth, key, invalidation, and stale policy depth.
- Use `message-queue-design`, `domain-event-modeling`, or `event-driven-architecture` for event and consumer contracts.
- When a traced side-effect flow has duplicate risk and routes to idempotency-retry-design, first inventory task-local replay sources that can reach the effect. Sources include clients, transports, brokers, workers, operators, and recovery paths. Record unknown or external replays.
- Use `failure-contract-design` for surfaced error semantics after failure points are named.
- Use `security-privacy-gate` when effects persist, cache, publish, log, or emit sensitive data.
