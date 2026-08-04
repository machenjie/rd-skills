# Async Job Design Benchmarks And Patterns

Load this reference when runtime durability, retry/terminal behavior, idempotency, enqueue/ack ordering, scheduling, replay, or operator recovery changes the job design. Do not load it for synchronous work whose loss and side effects are already accepted.

## Runtime Selection

| Runtime | Use when | Reject or escalate when | Required proof |
| --- | --- | --- | --- |
| In-process task/thread | Work is short, restart loss is acceptable, and no durable user outcome depends on it. | Retry, status, shutdown completion, or side effects matter. | Explicit loss/shutdown contract. |
| Scheduler/cron | Work is periodic reconciliation, cleanup, report, or polling. | Event reaction or overlapping ticks need durable coordination. | Overlap, missed-run, timezone, heartbeat, and idempotent-window behavior. |
| Queue worker | Durable decoupling, backpressure, fan-out, or delayed retry is needed. | Long branching workflow state or compensation dominates. | Durable enqueue, idempotent handler, ack/nack, terminal state, and replay. |
| Event consumer | Replayable log, ordering/partition, or multiple consumer groups are central. | Per-item progress or orchestrated compensation is primary. | Commit after durable effect, dedupe, schema/version, and ordering guard. |
| Workflow engine | Durable timers, branches, human waits, or long-lived compensation justify its operational cost. | A bounded job can meet the same failure contract more simply. | Version/replay compatibility and activity idempotency. |
| Managed/FaaS trigger | Bursty bounded work benefits from platform scaling. | Runtime, cold start, concurrency, or unit cost violates current limits. | Timeout/visibility alignment, concurrency cap, idempotency, and cost evidence. |

## Failure And Retry Semantics

| Failure | Treatment | Terminal/validation condition |
| --- | --- | --- |
| Transient network/timeout/5xx | When this failure is selected as retryable, keep retries inside a named attempts/deadline/cost budget, with jitter or provider guidance. | Exhaustion reaches the configured owned terminal outcome; prove the applicable failure path with a safe test or rehearsal, or record it as not run with a residual owner. |
| Rate/quota limit | Respect provider delay and reduce concurrency or pause when pressure persists. | No hot retry loop; quota owner and resume condition are named. |
| Validation/business rejection | Do not retry unchanged work. | Typed permanent result or quarantine preserves safe diagnostics. |
| Poison schema/payload | Quarantine the original envelope without blocking later work. | Version/failure class, owner, retention, and replay path exist. |
| Conflict/unknown outcome | Re-read or reconcile by business/idempotency key before retry. | Concurrent/timeout fixture proves one visible outcome or an owned manual recovery. |
| Circuit/dependency unavailable | Delay, pause, or shed according to job criticality and deadline. | Recovery does not synchronize a retry storm or overrun downstream capacity. |

Retries preserve the original job/message identity plus trace, correlation and causation context through terminal handling.

## Idempotency, Enqueue, And Ack Boundary

- Bind the logical key to operation, caller, tenant or resource scope, and payload identity, excluding changed meaning and covering the full retry or replay window.
- Prefer a conditional write or natural unique key; otherwise persist processing/committed/failed state and the reusable result before or atomically with the effect.
- When source state and work must agree, use a transaction/outbox or name the cleanup/recovery scan for the chosen enqueue order. If neither enqueue-first nor commit-first is recoverable, keep the action synchronous or redesign the boundary.
- Worker order is validate version → claim/dedupe → durable effect → status/compensation state → ack/offset commit. Ack-before-effect loses work; effect-before-ack without dedupe duplicates it.
- Broker “exactly once” does not cover database, payment, email, file, webhook, or other external effects.

## Workflow, Recovery, And Proof

| Concern | Decision and evidence |
| --- | --- |
| Saga/workflow | Orchestration names one visible step/status/compensation owner; choreography requires event ownership and stuck-saga detection. Persist version/timeout state; compensators are ordered/idempotent and rolling deploy handles in-flight versions. |
| Backfill/reconciliation | Chunk by owned scope, checkpoint after a durable boundary, throttle shared resources, compare source truth, and resume safely. |
| Cancellation/replay | Stop only at a safe boundary; preserve causality; rate-limit by tenant/resource and watch downstream saturation. |
| Observability/runbook | Bound labels; expose age/depth, outcome/failure class, duration, retry/replay, heartbeat, duplicate/conflict, and DLQ signals that map to pause/replay/quarantine/compensate actions. |
| Freshness/proof limit | Inspect current producers, handlers, status models, configs, tests, and runbooks; local tests do not prove broker, provider, live capacity, or production replay behavior. |

Route broker topology to message-queue-design and key/retry math to idempotency-retry-design. Route commit/effect order to transaction-consistency or data-side-effect-flow-tracing, and event semantics to domain-event-modeling. Route capacity to performance-budgeting and telemetry/runbooks to observability or reliability-observability-gate. Route sensitive payload/identity risk to security-privacy-gate.

Reject fire-and-forget durable outcomes, success before enqueue commit, unversioned long-lived payloads, cross-tenant priority starvation, unowned DLQs, process-kill cancellation, latest-code-only workflow replay, overlapping side-effecting ticks, and full-speed bulk replay.
