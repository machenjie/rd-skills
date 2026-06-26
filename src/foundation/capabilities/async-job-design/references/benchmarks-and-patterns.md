# Async Job Design Benchmarks And Patterns

Use this reference when `async-job-design` needs more depth than the main `SKILL.md` can carry efficiently. Keep the main body focused on routing, lifecycle decisions, output, and gates; use this file for runtime choices, failure matrices, idempotency patterns, scheduling/backfill concerns, graph-memory-execution coupling, validation matrices, and anti-pattern review.

## Table Of Contents

- Benchmark anchors
- Runtime selection matrix
- Retry and failure classification
- Idempotency strategy
- Durable enqueue and ack boundary
- Workflow, scheduling, and replay patterns
- Observability and runbook evidence
- Graph, memory, and execution coupling
- Job-to-validation matrix
- Anti-patterns to reject
- Handoff boundaries

## Benchmark Anchors

- **At-least-once delivery semantics:** Kafka, SQS, RabbitMQ, Pub/Sub, Service Bus, Redis Streams, and common schedulers can redeliver work.
- **Exactly-once illusion:** broker transactions do not make database writes, payments, emails, object storage writes, or webhooks exactly once. Idempotent workers provide the application guarantee.
- **Transactional Outbox / Inbox:** persist source state and work item in one transaction; consumers record processed keys before ack/commit.
- **Dead Letter Channel and Poison Message:** quarantine unrecoverable work with original payload, headers, failure class, attempts, and owner.
- **Saga and Compensating Transaction:** persist step state and run idempotent compensators for committed side effects.
- **Workflow replay/versioning:** Temporal, Cadence, Step Functions, Airflow, and Camunda require compatibility rules for in-flight work.
- **OpenTelemetry:** propagate `traceparent` and correlation/causation identifiers across producer, broker/scheduler, worker, and downstream calls.
- **Full-jitter retry:** use randomized exponential backoff to avoid synchronized retry storms.
- **SRE error-budget practice:** async freshness, job success, DLQ depth, and oldest-job age are user-impacting reliability signals.
- **Little's Law:** worker count and in-flight limits derive from arrival rate multiplied by service time.

## Runtime Selection Matrix

| Runtime | Pick when | Avoid when | Professional obligation |
| --- | --- | --- | --- |
| In-process task, goroutine, asyncio task, thread pool | Loss is acceptable, work is short, no human-visible outcome. | Restart loss, retries, status, or side effects matter. | State loss acceptance and shutdown behavior. |
| Cron or scheduled job | Periodic reconciliation, cleanup, reports, or polling. | Event reaction, sub-minute latency, or long overlap-sensitive ticks. | Lock/overlap policy, missed-run policy, heartbeat, idempotent window. |
| Queue worker | Decoupling, fan-out, backpressure, side-effecting work, delayed retry. | Complex long-running workflow state or branchy compensation dominates. | Durable enqueue, idempotent handler, ack/nack, DLQ, replay. |
| Event broker consumer | Replayable event log, multiple consumer groups, high throughput. | Per-item status, visible job progress, or orchestrated compensation is primary. | Offset commit after durable effect, consumer dedupe, partition/ordering guard. |
| Workflow engine | Durable timers, branching, human wait, compensation, months-long execution. | Tiny jobs or low-value work where engine operation is heavier than risk. | Workflow version pinning, activity idempotency, replay compatibility. |
| FaaS queue trigger | Spiky workload, simple bounded work, ops offload. | Sustained high volume, cold-start-sensitive path, runtime exceeds limits. | Idempotency per invocation, timeout vs visibility, concurrency and cost cap. |

## Retry And Failure Classification

| Failure class | Retry behavior | Terminal behavior | Validation signal |
| --- | --- | --- | --- |
| Transient network, 5xx, timeout | Exponential backoff with full jitter, bounded attempts and deadline. | DLQ with diagnostic after exhaustion. | Forced timeout/error reaches retry then DLQ. |
| Rate limit or quota | Respect `Retry-After` or use longer capped backoff. | DLQ or paused queue with owner if quota persists. | 429 fixture proves delay and no retry storm. |
| Permanent validation/business failure | Do not retry. | Failed permanent / DLQ with reason. | 4xx or invalid payload goes terminal immediately. |
| Poison schema/deserialization failure | Do not loop identical payload on main queue. | Quarantine with raw envelope and alert. | Malformed payload does not block later work. |
| Downstream circuit open | Pause, delayed requeue, or shed non-critical work. | Terminal after SLO/deadline breach. | Circuit-open path avoids hot retry loop. |
| Optimistic conflict | Re-read and retry shortly when safe. | Conflict/failed state after bounded attempts. | Concurrent execution fixture leaves one durable outcome. |
| Unknown outcome after timeout | Reconcile by idempotency key or external reference before retry. | Manual recovery if reconciliation is unavailable. | Timeout recovery proves no duplicate side effect. |

Retry policy checklist:

- `max_attempts`, `max_elapsed_time`, `base_delay`, `max_delay`, jitter algorithm, and retry budget are named.
- Retryable and non-retryable classes are explicit.
- Retry cost is modeled for paid APIs, LLM calls, warehouse scans, storage writes, and webhook fan-out.
- Retries preserve trace/correlation ids.

## Idempotency Strategy

```
Does the job have side effects that must occur once per logical unit?
  No -> document read-only or loss-accepted behavior.
  Yes ->
    Can the effect be a conditional write?
      Yes -> unique key, version check, PUT-if-absent, or natural business key.
      No ->
        create an idempotency record:
          key, job_name, tenant/resource scope, payload_hash, status, result, expires_at
        lock or insert before side effect;
        return stored result on duplicate;
        reject same key with different payload;
        retain beyond retry and replay window.
```

Common key sources:

| Key source | Suitable when | Guardrail |
| --- | --- | --- |
| Business natural key | Invoice PDF, entitlement grant, one output per resource. | Unique constraint and payload conflict behavior. |
| Request operation id | API-initiated async work. | Generated once per operation, not per retry. |
| Message/event id | Queue/event consumer. | Consumer inbox table or processed-key store. |
| External reference id | Payment, webhook, partner mutation. | Reconcile remote state before retry. |
| Tenant + range + job type | Reconciliation or backfill chunk. | Checkpoint and re-run semantics. |

## Durable Enqueue And Ack Boundary

Producer-side decision:

- If source state and job must both happen, prefer transactional outbox.
- If broker enqueue happens first, define cleanup for abandoned work when source state does not commit.
- If source state commits first, define recovery scan for missing jobs.
- If neither ordering is safe, keep synchronous or redesign the boundary.

Worker-side decision:

```
receive/claim work
  -> load and validate payload/schema version
  -> create or check idempotency/inbox record
  -> perform durable side effects
  -> persist status/result/compensation state
  -> ack/delete/commit offset
```

Ack before durable side effect creates lost work. Ack after side effect without idempotency creates duplicate risk on crash before ack. Safe designs make both outcomes visible and recoverable.

## Workflow, Scheduling, And Replay Patterns

| Pattern | Professional requirement |
| --- | --- |
| Saga orchestration | Persist step state, timeout, compensation, and idempotent compensators. |
| Saga choreography | Each event consumer names retry, compensation event, and stuck-saga detection. |
| Workflow engine | Pin version for in-flight work; add patch/upcaster/drain plan before deploy. |
| Cron / scheduler | Prevent overlap, define missed tick behavior, use UTC or explicit timezone, and emit last-success heartbeat. |
| Backfill / bulk job | Chunk by tenant/range, checkpoint after durable boundary, throttle shared resources, and resume idempotently. |
| Reconciliation job | Compare source of truth to derived/external state, record drift, and make remediation idempotent. |
| Replay after bug fix | Rate-limit by tenant/resource, preserve original causality, and monitor downstream saturation. |

## Observability And Runbook Evidence

Minimum signal set:

- enqueue rate, queue depth, in-flight count, worker concurrency, oldest pending/in-flight age;
- success/failure/cancel/timeout/DLQ counts by bounded failure class;
- queue latency, execution duration, p50/p95/p99, retry count, replay count;
- last successful run/heartbeat for scheduled jobs;
- idempotency duplicate and payload-conflict counts;
- downstream rate-limit/circuit-open counts;
- DLQ depth, oldest DLQ age, and replay throughput;
- structured logs with job name/id, attempt, tenant/resource scope, idempotency key or hash, correlation id, trace id, status transition, and failure class.

Runbook evidence:

- trigger: which alert or dashboard signal starts triage;
- expected output: how to tell the job, DLQ, or replay is healthy;
- safe actions: pause, resume, replay, quarantine, skip, compensate, or rollback;
- unsafe actions: replay without rate limit, manual status edits, deleting DLQ payloads without archive;
- owner, escalation, retention, and post-incident reconciliation.

## Graph, Memory, And Execution Coupling

| Evidence source | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current enqueue sources, worker handlers, configs, tests, status models, and runbooks are inspected. | Graph proximity is used as proof without source confirmation. |
| Project memory | Prior incident, fragile file, or runbook fact has timestamp, path, owner, and unchanged source. | Memory predates job, schema, queue, runbook, or validation changes. |
| Execution trajectory | Validation, review, and repair order is after final material edit. | Tests ran before job/retry/DLQ/status changes or after unreviewed repair. |
| Generated reports | Score/audit/build report is used as selector for improvement area. | Report is treated as source truth or live behavior evidence. |
| Dashboard/telemetry | Metric source, environment, labels, and time window are bounded. | High-cardinality labels or stale dashboard screenshots hide current behavior. |

## Job-To-Validation Matrix

| Job concern | Example validation |
| --- | --- |
| Durable enqueue | Transaction/outbox test: source state and job commit/rollback together. |
| Duplicate delivery | Same job/message runs twice and produces one side effect/result. |
| Ack crash boundary | Crash before ack does not lose work; crash after side effect does not duplicate effect. |
| Retry exhaustion | Transient failure retries with jitter and reaches owned terminal state. |
| Poison payload | Malformed payload quarantines and later jobs continue. |
| Cancellation | Cancellation at safe point stops new side effects and records terminal status. |
| Compensation | Failure after committed step runs compensator in order and is idempotent. |
| Replay | DLQ/replay path reprocesses safely with tenant/resource throttle. |
| Cron overlap | Long tick does not double-run side effects. |
| Deploy skew | Old payload/workflow version survives rolling deploy or drains safely. |
| Observability | Metrics/logs/traces include bounded labels and alertable terminal states. |
| Cost/capacity | Load/backlog drain test or budget proves worker count, RSS, CPU, and retry cost bounds. |

## Anti-Patterns To Reject

| Anti-pattern | Why it fails |
| --- | --- |
| `fire_and_forget(send_email(user))` in a request handler. | Lost on restart, no retry, no status, no owner. |
| Returning success when only enqueue was attempted but not committed. | User sees completion while work may not exist. |
| Retrying `POST /charge` without idempotency key. | Duplicate charges under timeout or redelivery. |
| Snapshot payload plus multi-day retry window with no schema version. | Stale data or deserialization failure after deploy. |
| One queue for all tenants and all priorities. | Bulk work starves critical transactional work. |
| DLQ with no alert or replay runbook. | Silent failure and unrecoverable backlog. |
| Ack before durable write. | Crash loses the message permanently. |
| Cancellation by killing process. | Leaves partial external side effects and no compensation. |
| Workflow versioned by latest deploy. | In-flight replay corrupts or crashes. |
| Cron overlap allowed for side-effecting ticks. | Double effects under slow run or clock drift. |
| Replay all DLQ at full speed after a fix. | Downstream dependency melts during recovery. |

## Handoff Boundaries

- Use `message-queue-design` for broker topology, partition keys, offset commits, visibility timeout config, and DLQ infrastructure.
- Use `idempotency-retry-design` for key scope, payload hash, retry budget, circuit breaker, and duplicate-side-effect math.
- Use `transaction-consistency` and `data-side-effect-flow-tracing` for outbox, saga ordering, hidden side effects, and commit boundaries.
- Use `domain-event-modeling` for event fact semantics, schema contract, producer/consumer inventory, and replay-safe event design.
- Use `performance-budgeting` for wall-clock window, worker count, queue depth, CPU/RSS, replay, and unit-cost budgets.
- Use `reliability-observability-gate` and `observability` for SLI/SLO, dashboard, alert, runbook, and incident readiness.
- Use `security-privacy-gate` and `permission-boundary-modeling` for sensitive payloads, service-account scope, tenant isolation, and audit.
- Use `quality-test-gate` and `validation-broker` when changed job paths need executable failure-injection evidence or stale-validation repair.
