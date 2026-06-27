---
name: async-job-design
description: Designs durable asynchronous jobs with enqueue-after-commit, idempotency, bounded retry, timeout, status visibility, cancellation, compensation, observability, and recovery.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "43"
changeforge_version: 0.1.0
---

# Mission

Design asynchronous jobs that execute safely after the initiating request returns: duplicate delivery, retries, timeouts, cancellation, partial failure, poison messages, deploy skew, operator replay, and tenant/resource contention must have bounded, visible, recoverable outcomes.

# When To Use

Use this capability when a change adds or modifies background jobs, queue workers, scheduled/cron jobs, delayed tasks, batch processors, fan-out/fan-in jobs, long-running workflows, async user flows, durable job status, data imports/exports, async webhook senders, reconciliation jobs, cleanup jobs, or compensation workers. Use it when a request returns `202 Accepted`, "queued", or "processing" while meaningful work finishes later.

# Do Not Use When

Do not use this capability to move work out of the request path "to make it fast" without defining durable enqueue, ownership, idempotency, retry policy, status visibility, failure handling, and recovery. Do not use it as the primary owner for queue topology (`message-queue-design`), event fact contracts (`domain-event-modeling`), broker selection (`event-driven-architecture`), retry math alone (`idempotency-retry-design`), or schema migration plans (`data-migration-design`); use those alongside this capability when their boundary dominates.

# Boundary And Source Truth

This capability owns the job lifecycle: trigger, durable enqueue, payload, worker execution, status model, retry/DLQ/replay, cancellation, compensation, observability, ownership, and validation. It does not own broker infrastructure, domain-event semantics, queue partition topology, API response contracts, or data migration sequencing except as handoff boundaries.

Source truth is current job/worker code, enqueue call sites, scheduler or broker config, status schema, idempotency store, runbooks, dashboards, tests, validation output, and current registry/routing entries. Repository graph, project memory, generated reports, old runbooks, and prior validations are selectors only until current source inspection and post-edit validation confirm them. Do not edit generated `dist/` or installed runtime copies as source.

# Stage Fit

- **Planning:** decide whether async work is needed, name the durable job boundary, and reject fire-and-forget or "queued equals done" designs.
- **Coding / review:** verify enqueue-after-commit, payload versioning, idempotency, ack/nack, cancellation checks, compensation, and worker version compatibility.
- **Testing:** map duplicate delivery, timeout, retry exhaustion, poison message, cancellation, replay, and deploy-skew paths to executable or explicitly not-run evidence.
- **Release / operations:** require queue depth, lag, DLQ, oldest job age, heartbeat, alert owner, runbook, replay throttle, and rollback or drain strategy.

# Non-Negotiable Rules

- Jobs define `job_name`, trigger, owner, payload schema/version, idempotency key, retry policy, timeout/deadline, failure classes, DLQ/quarantine, status model, cancellation, compensation, observability, and replay procedure.
- A request is not accepted as durable until the job is durably enqueued. If business state and enqueue are not atomic, use transactional outbox, CDC, or a recovery scan with an explicit residual risk.
- Payloads carry stable identifiers, tenant/resource scope, correlation/trace id, and schema version. Snapshots require `snapshot_taken_at`, expiry semantics, and compatibility handling.
- Workers tolerate at-least-once delivery, duplicate execution, out-of-order execution, concurrent execution, deploy skew, and replay unless the selected infrastructure and validation prove a narrower guarantee.
- Side effects inside jobs are idempotent by natural key, conditional write, idempotency store, or downstream idempotency key. Otherwise the design must block retry/replay for that side effect.
- Retries are bounded by max attempts, max wall-clock, exponential backoff with jitter, retryable vs non-retryable classification, and an owned terminal state.
- Per-attempt timeout, total deadline, and visibility/lease timeout are ordered explicitly. A worker must not run longer than the lease without renewal.
- Status is queryable by the actor who needs it: user, support, operator, dependent system, or all of them. Silent terminal failure is not allowed.
- Cancellation is cooperative and checked at safe points. The design states what cancellation does and does not undo.
- Compensation is a design output for committed multi-step side effects; non-compensatable effects are escalated before shipping.
- DLQ or quarantine is an owned recovery surface: alert, runbook, retention, triage fields, and rate-limited replay are required.
- Structured logs and metrics include job name/id, attempt, idempotency key, correlation/trace id, status transition, failure class, queue age, execution duration, retry count, DLQ depth, and oldest in-flight age with bounded label cardinality.
- Jobs touching money, identity, notifications, inventory, tenant-wide data, user data bulk changes, external partners, or irreversible side effects require reconciliation and stronger validation.

# Industry Benchmarks

Anchor against at-least-once delivery, idempotent consumers, transactional outbox/inbox, DLQ and poison-message handling, Saga and compensating transactions, workflow-engine replay/versioning, OpenTelemetry trace propagation, full-jitter retry, SRE error budgets, Little's Law for worker capacity, and runbook-backed recovery. Use [references/checklist.md](references/checklist.md) for quick design review, [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for runtime selection and failure matrices, and [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on graph/memory/execution freshness, tool permission boundaries, validation artifacts, or evidence limits.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Best-effort in-process task | Short, low-value, loss acceptable, no external side effect. | Make loss explicit and keep it off critical outcomes. | Loss acceptance, shutdown behavior, no-user-impact proof. | `language-performance-safety` | Durable queue/workflow engine. |
| Durable queue worker | Broker/queue worker, webhook sender, notification, import/export, side-effecting consumer. | Durable enqueue, idempotency, ack/nack, retry, DLQ, replay, status. | Enqueue boundary, payload schema, ack point, duplicate/retry/DLQ tests. | `message-queue-design`, `idempotency-retry-design` | Exactly-once claims without dedupe proof. |
| Scheduled/reconciliation job | Cron, periodic cleanup, reconciliation, delayed task, report job. | Overlap prevention, drift, missed tick recovery, idempotent range processing. | Scheduler lock, checkpoint/window, rerun behavior, last-success heartbeat. | `performance-budgeting`, `observability` | `concurrencyPolicy: Allow` for side-effecting ticks. |
| Long-running workflow / saga | Durable timers, branching, external steps, months-long execution, compensation. | Version pinning, step state, cancellation, compensation, replay safety. | Workflow version plan, step log, compensators, replay/drain strategy. | `transaction-consistency`, `release-rollback` | Latest-code replay for in-flight workflows. |
| Bulk/backfill/import/export job | High volume, tenant-wide data, file generation, warehouse/ETL, replay/retry after fix. | Chunking, checkpoints, tenant isolation, resource budget, rate-limited replay. | Volume, checkpoint, per-tenant cap, CPU/RSS/queue budget, recovery test. | `data-migration-design`, `performance-budgeting` | Load-all or unbounded fan-out. |
| Async UX/status flow | `202 Accepted`, polling, progress screen, completion notification, support status. | Separate accepted, running, durable success, timeout, failed, cancelled, replayed. | Status source, visible terminal states, retry safety, user/support messaging. | `interaction-state-modeling`, `frontend-api-integration` | Success toast before durable completion. |

# Selection Rules

Select this capability when background execution lifecycle is primary: when, where, how, who owns it, what happens when it fails, and how recovery is proven. Prefer `idempotency-retry-design` when key/retry math is the headline. Prefer `message-queue-design` when broker topology, ordering, partitioning, or queue config dominates. Prefer `domain-event-modeling` when durable fact semantics and schema contract dominate. Prefer `data-migration-design` for migration/backfill sequencing. Prefer `degradation-circuit-breaking` when downstream protection patterns dominate. Pair with `reliability-observability-gate` for production SLO and alert acceptance.

# Proactive Professional Triggers

- **Signal:** a request handler starts `fire_and_forget`, goroutine/task/thread, or local timer for meaningful work. **Hidden risk:** process restart or deploy loses work with no retry or status. **Required professional action:** require durable enqueue or explicit best-effort acceptance. **Route to:** `async-job-design`, `reliability-observability-gate`. **Evidence required:** enqueue boundary, loss acceptance or durable handoff, shutdown behavior.
- **Signal:** API returns `202`, "queued", "processing", or success before durable completion. **Hidden risk:** users and clients treat accepted work as done and retry unsafely. **Required professional action:** define status model, completion signal, timeout/cancel behavior, and idempotent retry. **Route to:** `interaction-state-modeling`, `idempotency-retry-design`. **Evidence required:** status source, visible terminal states, duplicate-submit test.
- **Signal:** business state is saved and job enqueue/publish happens in a separate step. **Hidden risk:** committed state with no job, or job for rolled-back state. **Required professional action:** require outbox/CDC/equivalent or recovery scan. **Route to:** `transaction-consistency`, `data-side-effect-flow-tracing`. **Evidence required:** transaction boundary, outbox/relay owner, lost-enqueue validation.
- **Signal:** visibility timeout, lock lease, cron interval, or scheduler concurrency is shorter than worst-case execution. **Hidden risk:** same job runs concurrently or scheduled ticks overlap. **Required professional action:** set lease renewal, concurrency policy, checkpoint, and overlap handling. **Route to:** `concurrency-control`, `message-queue-design`. **Evidence required:** timeout inequality, lease renewal, overlap test.
- **Signal:** retry, DLQ, replay, or poison handling exists without owner, alert, retention, triage fields, or replay throttle. **Hidden risk:** failure becomes silent backlog or replay storm. **Required professional action:** make DLQ a runbook-backed recovery surface. **Route to:** `observability`, `reliability-observability-gate`. **Evidence required:** DLQ metrics, oldest age, alert owner, replay procedure.
- **Signal:** job payload is a stale snapshot, unversioned JSON blob, or raw domain object. **Hidden risk:** delayed execution commits obsolete facts or crashes after schema deploy. **Required professional action:** use stable ids or declare snapshot/version expiry. **Route to:** `dto-schema-design`, `version-compatibility`. **Evidence required:** payload schema version, expiry, compatibility test.
- **Signal:** long-running workflow or workflow engine code changes while in-flight work exists. **Hidden risk:** replay corruption or activity signature mismatch. **Required professional action:** pin workflow versions, patch replay, drain old runs, or document compatibility. **Route to:** `release-rollback`, `transaction-consistency`. **Evidence required:** versioning plan, replay/drain evidence, rollback limit.
- **Signal:** repository graph, project memory, runbook, or previous validation says the job is safe without current source and command-order confirmation. **Hidden risk:** stale topology, hidden consumer, or validation before final edit. **Required professional action:** reconcile graph/memory/trajectory against current source and validators. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, `validation-broker`. **Evidence required:** inspected paths, accepted/rejected memory, validation freshness.

# Risk Escalation Rules

Escalate when jobs affect money, inventory, identity, customer notifications, tenant-wide data, regulated records, external systems without their own idempotency, irreversible side effects, workflows longer than one deploy window, high fan-out, per-tenant billing, or unknown failure SLOs. Escalate when no owner can be named for DLQ, replay, status, runbook, or compensation.

# Critical Details

Async work changes the failure model: the initiating request can succeed while the job later fails, duplicates, times out, is cancelled, or runs after code changes. Apply these checks:

- Durable enqueue is a consistency boundary; "save then publish" without outbox or recovery is a dual-write risk.
- Ack/commit happens after durable side effects, not before. Otherwise crashes create lost work.
- Idempotency records must retain results beyond the retry/replay window and reject same key with incompatible payload.
- Backpressure protects dependencies; producer throttle, per-tenant caps, and bounded worker concurrency are part of correctness.
- Replays are operational releases. They need rate limits, tenant scoping, idempotency, and observability.
- Cron needs overlap policy, missed-run policy, time-zone/clock-skew treatment, and last-success heartbeat.
- Workflow engines reduce orchestration burden but do not make activities, external calls, or compensation automatically idempotent.
- Cost is a reliability signal: retry storms and backlog drains can multiply paid API, LLM, warehouse, storage, and egress costs.

# Failure Modes

- **Duplicate side effect:** worker retries a non-idempotent charge, email, webhook, or inventory update and creates customer-visible duplicates.
- **Lost durable handoff:** request returns success before durable enqueue; producer crashes and the job never exists.
- **Invisible terminal state:** job status is not queryable, so users retry repeatedly and support cannot answer whether work ran.
- **Stale payload snapshot:** multi-day retry uses obsolete payload data after source state or schema changed.
- **Poison retry loop:** permanent validation failure burns retries and floods the DLQ with the same defect.
- **Partial cancellation:** cancellation stops the process mid-step while committed external effects have no compensation.
- **Silent DLQ backlog:** DLQ accumulates because no alert, triage owner, retention, replay throttle, or oldest-age metric exists.
- **Lease overlap:** visibility timeout expires during execution and a second worker runs the same job concurrently.
- **Deploy-skew replay break:** rolling deploy changes payload or activity code while old work is in flight and replay fails.
- **Tenant replay starvation:** one tenant's bulk job starves other tenants or melts a shared dependency during replay.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 routing, boundaries, mode selection, output shape, and quality gates. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete job design, worker change, scheduled job, transactional enqueue, retry/DLQ/replay policy, cancellation, compensation, deploy skew, or production observability. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when detailed runtime selection, retry/failure matrices, idempotency trees, scheduling/backfill patterns, observability/runbook matrices, graph-memory-execution coupling, or validation matrices are needed. Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on accepted or rejected graph/memory claims, tool permission boundaries, validator output, exit code, report/artifact paths, validation freshness, or what async evidence does and does not prove. Use [examples/example-output.md](examples/example-output.md) only when the output shape is unclear. Do not load deep references for isolated best-effort tasks where loss is accepted and no external side effect exists.

# Output Contract

Return an async job design containing:

- `mode_selected` with trigger signal.
- `boundaries_inspected`: enqueue source, worker code, scheduler/broker config, status store, idempotency store, tests, runbooks, dashboards, registry/routing, and skipped boundaries.
- `source_evidence`: current source, repository graph, project memory, runbook, dashboard, prior validation, and execution trajectory accepted, rejected, stale, or not verified.
- `job_name`, `trigger`, `owner`, `runtime`, and alternatives rejected.
- `payload_schema` with schema version, stable identifiers, tenant/resource scope, snapshot decision, expiry, and compatibility rule.
- `durable_enqueue`: transaction boundary, outbox/CDC/recovery scan, and request acknowledgement point.
- `delivery_semantics`: at-most-once, at-least-once, or exactly-once claim plus the idempotency compensation that makes it true.
- `ack_nack_boundary`: acknowledgement/offset/delete point, crash-before/after behavior, visibility/lease renewal, and poison-message path.
- `idempotency`: key derivation, scope, storage, TTL/retention, payload conflict behavior, replay semantics, and downstream idempotency proof or residual risk.
- `concurrency`: max worker concurrency, per-tenant cap, ordering or partition key, downstream rate limit, backpressure, and noisy-tenant isolation.
- `timeouts`: per-attempt timeout, total deadline, visibility/lease timeout, scheduler interval, cancellation deadline, and renewal behavior.
- `retry_policy`: failure classes, backoff formula, jitter, max attempts, max wall-clock, terminal state, and retry cost cap.
- `failure_handling`: DLQ/quarantine, triage fields, alert thresholds, runbook, replay throttle, retention, and owner.
- `cancellation` and `compensation`: signal mechanism, safe points, guarantees, compensator ordering, and idempotency of compensators.
- `status_model`: states, transitions, visibility to users/support/operators/dependent systems, and query/API contract.
- `observability`: metrics, structured log fields, traces, label cardinality, dashboard, alert owner, and last-success heartbeat.
- `versioning_release`: payload evolution, workflow versioning, rolling deploy/drain strategy, rollback limits, and in-flight compatibility.
- `cost_capacity_model`: volume, wall-clock window, CPU/RSS, queue/backlog bounds, worker count, replay cost, and retry-storm cost.
- `job_to_validation_map`: duplicate, transactional enqueue, ack crash, retry, DLQ, replay, cancellation, compensation, deploy skew, status, and observability validation or residual risk.
- `evidence_limits`: what the evidence proves, what remains unproven, residual owner, and next gate.

# Evidence Contract

Close an async job design only when these answers are concrete:

- **Basis:** mode selected, job boundary, trigger, owner, side effects, tenant/resource scope, and why async execution is required instead of synchronous completion.
- **Current evidence:** source paths, config, status schema, idempotency store, runbooks, dashboards, graph slice, memory signals, and validation trajectory inspected with freshness status.
- **Lifecycle judgment:** durable enqueue, delivery semantics, ack/nack, retry/DLQ, replay, ordering/concurrency, cancellation, compensation, deploy skew, observability, and cost/capacity decisions.
- **Validation evidence:** validation commands, tests, fixtures, validator output, exit code, artifact or report path, or explicit not-run disclosures mapped to duplicate delivery, enqueue atomicity, retry exhaustion, DLQ, replay, cancellation, compensation, status visibility, and stale-validation repair.
- **What evidence proves / does not prove:** bounded retries, visible terminal states, owned recovery, and tested failure paths; plus unproven production broker behavior, clock skew, ordering, downstream idempotency, replay scale, or tenant skew.
- **Handoff and residual risk:** unresolved queue topology, retry math, transaction consistency, security/privacy, performance budget, release rollback, or observability readiness assigned to the next gate with owner.

# Quality Gate

The job design passes only when:

1. Duplicate delivery, retry exhaustion, timeout, cancellation, partial failure, poison message, replay, and deploy skew each have defined outcomes with diagnostics.
2. Durable enqueue is atomic with source state or has an explicit outbox/CDC/recovery scan and residual risk.
3. Idempotency is proven by natural idempotence, conditional write, key/store/replay semantics, or explicit non-retryable restriction.
4. Ack/commit/delete happens after durable side effects, and crash-before/after behavior is stated.
5. Visibility/lease timeout exceeds per-attempt timeout with safety margin, or renewal is implemented for long jobs.
6. Retry policy is bounded, jittered, failure-classified, and cost-aware.
7. DLQ/quarantine has owner, alert, triage fields, retention, runbook, and replay throttle.
8. Status is queryable by the humans or systems that need it.
9. Cancellation and compensation are implemented and tested where side effects can partially commit.
10. Concurrency caps, backpressure, and tenant/resource isolation protect downstream dependencies.
11. Trace context propagates producer -> broker/scheduler -> worker, with bounded metric labels.
12. Payload schema/version and deploy strategy protect in-flight work during rolling releases.
13. Cost and capacity are modeled for projected volume, backlog drain, and retry storm.
14. Job-to-validation map covers success plus failure-injection paths or names not-verified residual risk.
15. Graph, memory, runbook, generated report, and prior validation claims are reconciled against current source and post-edit command order.
16. Validation evidence includes command, validator output, exit code, artifact/report path, what the evidence proves, what it does not prove, and residual owner when a check is not run.

# Benchmark Coverage

This capability covers async job lifecycle, durable enqueue, idempotency, retry/DLQ/replay, ack/nack, status visibility, cancellation, compensation, workflow versioning, cron/backfill/reconciliation safety, production observability, cost/capacity, graph-memory-trajectory freshness, and validation mapping. It does not by itself prove broker provisioning, event schema compatibility, API UX, migration rollout, or production readiness without the companion gates selected above.

# Routing Coverage

Routes from `backend-change-builder`, `data-middleware-change-builder`, `reliability-observability-gate`, `service-business-logic`, `interaction-state-modeling`, `user-flow-modeling`, `concurrency-control`, `transaction-consistency`, and `change-forge-router` should arrive here when background execution lifecycle and recovery behavior are primary. Route away when queue topology, event fact contract, duplicate-key math, API transport, migration sequencing, performance budget, or release rollout is the primary decision.

# Used By

- backend-change-builder
- data-middleware-change-builder
- reliability-observability-gate

# Handoff

Hand off to `idempotency-retry-design` for repeated side-effect math; `message-queue-design` for queue topology, partitioning, ack/offset configuration, and broker specifics; `domain-event-modeling` for durable fact semantics; `event-driven-architecture` for multi-service event flow; `logging-error-handling` for diagnostic context standards; `data-migration-design` for migration/backfill sequencing; `transaction-consistency` for outbox and saga consistency; `performance-budgeting` for wall-clock, CPU/RSS, queue, and cost budgets; `observability` and `reliability-observability-gate` for SLO and alerting acceptance; `security-privacy-gate` when payloads contain sensitive data or broad machine identity.

# Completion Criteria

The capability is complete when the job can run asynchronously with durable enqueue, safe retries, visible status, bounded failure behavior, recoverable partial failure, tested cancellation/compensation, deploy-skew compatibility, propagated tracing, owned DLQ/replay, and bounded cost at projected volume - and when an on-call engineer can diagnose and recover from a failure using the runbook and emitted observability.
