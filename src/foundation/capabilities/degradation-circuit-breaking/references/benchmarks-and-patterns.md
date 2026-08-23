# Degradation And Circuit-Breaking Benchmarks And Patterns

Load for a named dependency-criticality, ceiling, timeout/retry, circuit, fallback, isolation, shedding, or recovery-parameter decision. Consume gateway end-to-end, hop-deadline, and retry ceilings as immutable; without a gateway, derive equivalent local ceilings first.

## Dependency Criticality

| Role | Selected failure policy | Minimum evidence |
| --- | --- | --- |
| Correctness/security critical | Fail closed before unsafe state. | Typed unavailable outcome, no partial effect, owner, recovery. |
| Required user path | Bound wait and expose degraded/unavailable behavior. | Deadline allocation and rollback/retry semantics. |
| Optional/enrichment | Omit/default/cache only when truthful. | Degraded marker where material, freshness and permission owner. |
| Async/deferrable | Queue/defer with durable terminal ownership. | Enqueue/ack/idempotency and backlog recovery. |

## Parameter Decisions

| Decision | Derive from | Reject |
| --- | --- | --- |
| Chain/local ceiling | Gateway chain; otherwise caller/job objective, cancellation, amplification, rollback. | Extending or silently assuming a gateway ceiling. |
| Connection/read/phase timeout | Remaining ceiling, latency/queue/fan-out, cancellation, cleanup. | A phase beyond its ceiling or copied constant. |
| Retry/backoff/jitter | Ceiling, provider outcome, idempotency/reconciliation, load/cost, synchronized-client risk. | Retry-everything, implicit defaults, or amplification. |
| Circuit signal/window | Failure/latency class, volume, sampling window. | Low-volume noise or mixed classes. |
| Open/probe/close | Recovery expectation, probe safety/capacity, success criteria. | Side-effecting probes or recovery flood. |
| Fallback/isolation/shedding | Truthfulness, freshness, tenant/permission, capacity and invariant. | Hidden corruption/denial, cross-tenant data, unbounded queue. |

## Isolation, Recovery, And Proof

- Bound dependency pools, queues, fan-out, and concurrency before shared saturation.
- Name fallback source, acceptable staleness/quality, permission scope, degraded state, invalidation, and owner.
- Model fan-out and retry amplification; drop optional work only when product and audit semantics permit it.
- Test timeout/rate/5xx/slow/hung/partial outcomes, circuit transitions, cancellation cleanup, fallback age/permission, isolation, and recovery ramp after final edit.
- Local faults do not prove provider production behavior, traffic correlation, capacity, objective impact, or incident recovery; name residual owner.

Gateway ceilings stay with `network-protocol-gateway-usage`; idempotency/effect safety with `idempotency-retry-design`; lifecycle/pools with `dependency-wiring-lifecycle`; async backlog with `async-job-design`; capacity with `performance-budgeting`; telemetry/runbooks with `observability`; security-critical fallback with `security-privacy-gate`.
