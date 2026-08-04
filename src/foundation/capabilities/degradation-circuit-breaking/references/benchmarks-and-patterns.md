# Degradation And Circuit-Breaking Benchmarks And Patterns

Load this reference when dependency criticality, timeout budget, retry/circuit behavior, bulkhead/backpressure, fallback freshness or load shedding changes. Treat gateway-owned end-to-end, hop-deadline, and retry ceilings as immutable inputs. Derive dependency phase timeouts and actual retry policy beneath those ceilings from current traffic, SLOs, provider recovery, and fault tests; without a gateway chain, first derive equivalent local ceilings.

## Dependency Criticality

| Dependency role | Failure policy | Required evidence |
| --- | --- | --- |
| Correctness/security critical | Fail closed or stop before unsafe state. | Typed unavailable outcome, no partial side effect, owner and recovery path. |
| User-path required | Bound wait and return explicit degraded/unavailable behavior. | End-to-end deadline allocation and rollback/retry semantics. |
| Optional/enrichment | Omit/default/cache only when semantics remain truthful. | Caller-visible degraded marker where omission matters and freshness owner. |
| Async/deferrable | Queue/defer with durable status and terminal/reconciliation owner. | Enqueue/ack/idempotency and backlog recovery proof. |

## Timeout, Retry, And Circuit Parameters

| Parameter | Calibrate from | Reject when |
| --- | --- | --- |
| End-to-end, hop-deadline, and retry ceilings | Gateway-owned current chain; otherwise caller/job/SLO, cancellation, amplification, and rollback constraints for local ceilings. | Degradation extends, reallocates, or silently assumes a gateway-owned ceiling. |
| Dependency connection/read/phase timeouts | Remaining applicable hop budget, connection/response distribution, queueing, fan-out, cancellation and cleanup cost. | A phase timeout reaches beyond its ceiling or copied constants ignore path behavior. |
| Actual retry policy | Immutable retry/deadline ceilings, provider semantics, idempotency, unknown-outcome reconciliation, retry load and cost. | Retrying every status/error, exceeding a ceiling, or leaving attempts/backoff to implicit library defaults amplifies failure. |
| Backoff/jitter | Provider recovery/rate guidance and synchronized-client risk. | Fixed schedule is copied without traffic/fault evidence. |
| Circuit signal/window | Failure/latency class, meaningful request volume and sampling window. | Low-volume noise or mixed failure classes open/close incorrectly. |
| Open/half-open/close | Recovery expectation, probe safety/capacity and success criteria. | Probes cause side effects or recovery floods the dependency. |

Circuit breakers prevent repeated calls during a demonstrated failure mode; they do not replace timeout, authorization, idempotency, capacity planning or provider recovery. Cancellation releases sockets, transactions, pool slots and child work.

## Isolation, Degradation, And Proof

- Bound per-dependency pools, queues, fan-out and concurrency from capacity/deadline; apply admission, priority or load shedding before shared resources saturate.
- A fallback names source, maximum acceptable staleness/quality, permission/tenant scope, user-visible degraded state, invalidation and owner. Reject plausible-looking stale or cross-tenant data.
- Model total availability/latency impact across fan-out and retry amplification; optional work may be dropped only when product semantics and audit needs allow it.
- Validate forced timeout/rate/5xx/connection/slow/hung/partial cases, circuit transitions, cancellation/resource release, fallback age/permissions, queue/pool isolation and recovery ramp after final edit.
- Local fault tests do not prove provider production behavior, real traffic correlation, capacity, SLO impact or incident recovery; name residual owner.

Route gateway end-to-end, hop-deadline, and retry ceilings to `network-protocol-gateway-usage`; consume those limits here without redefining them. Route effect-safety and idempotency semantics to `idempotency-retry-design`; retain the dependency's actual retry policy here. Route pools and lifecycle to `dependency-wiring-lifecycle`. Route async backlog to `async-job-design`, capacity to `performance-budgeting`, and telemetry or runbooks to `observability`. Route security-critical fallback to `security-privacy-gate`.

Reject missing timeouts, per-call retries without a shared budget, and fixed universal circuit thresholds. Reject fallback that hides corruption or denial and unknown-outcome retries without idempotency, result lookup, or reconciliation. Reject unbounded queues, unsafe circuit probes, and recovery that releases all queued work at once.
