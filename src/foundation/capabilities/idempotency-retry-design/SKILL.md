---
name: idempotency-retry-design
description: Designs idempotency keys, bounded retries, duplicate detection, timeout outcomes, and terminal failure states for payments, order creation, webhooks, async consumers, and side-effecting external calls.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "42"
changeforge_version: 0.1.0
---

# Mission

Design side-effecting operations so **retries, duplicate delivery, and uncertain timeout outcomes cannot create duplicate charges, duplicate orders, duplicate notifications, or unbounded failure loops** — by establishing idempotency contracts at every write boundary, bounded retry policies per error class, and deterministic terminal states for every failure path.

# When To Use

Use this capability when a change includes: payment capture or refund operations; order or booking creation; webhook delivery to external parties; async consumer message processing; external API calls with write side effects; operations where the caller cannot distinguish "did not receive response" from "server did not process"; client-side form retry after network failure; or background job workers that process work from a queue at-least-once.

# Do Not Use When

Do not use this capability for read-only GET operations — reads are naturally idempotent. Do not use it as a substitute for correct failure handling: retry with idempotency does not eliminate permanent failures; those must surface to operators or users for resolution. Do not use it for in-process function calls within a single database transaction — the transaction boundary handles atomicity.

# Non-Negotiable Rules

- **Idempotency key defines a unique (key, operation, payload-hash) triple.** An idempotency key alone is not sufficient — the same key with a different payload must be detected and rejected (return 422 Unprocessable Entity). Silently processing a different payload for a known key is a silent data corruption vulnerability.
- **Timeout outcome is unknown; do not retry a mutation without an idempotency key.** When a write operation times out, the server may have committed the operation but the response was lost in transit. Retrying without an idempotency key creates a duplicate. Before retrying: check idempotency key first (has the operation already been processed?). If yes, return the cached outcome. If no, process and cache.
- **Retry is bounded.** Every retry policy must define: maximum attempt count, maximum total elapsed time (deadline), backoff algorithm (exponential with jitter), and a terminal state for permanent failure. Unbounded retry is not a resilience strategy — it is a resource exhaustion attack vector against your dependencies.
- **Retryable errors are a narrow explicit set.** Define which errors are retryable: transient network errors (connection reset, timeout), `429 Too Many Requests`, `503 Service Unavailable`. Non-retryable: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict` (indicates already processed — check the idempotency store), `422 Unprocessable Entity`. Never retry 4xx errors as if they might resolve with time.
- **Idempotency store retention window must exceed maximum retry deadline.** If your maximum retry deadline is 24 hours, your idempotency key store must retain keys for > 24 hours (recommended: 7 days). Keys that expire before the retry window creates re-processing vulnerabilities.
- **Dead-letter queue is the terminal state for persistent failures.** After exhausting retry budget, the operation must be moved to a DLQ (or equivalent dead-letter table) with: original operation payload, all error details, attempt count, timestamps. Never silently discard. DLQ events must trigger an alert to the owning team.
- **Reconciliation procedure is defined for timeout-then-retry.** For operations where the server may have committed but no response was received (payment capture, external write): define a reconciliation query (check by idempotency key or operation reference ID) before retrying. This is the correct mechanism for "at-most-once" guarantees in at-least-once infrastructure.

# Industry Benchmarks

Anchor this capability on idempotent API operation design, bounded retry with jitter, circuit breaker/retry budget, durable dedupe stores, and DLQ/reconciliation discipline. Load [references/industry-benchmarks.md](references/industry-benchmarks.md) only when release evidence, audit, or high-risk payment/webhook/queue retry behavior needs named benchmark support.

# Boundary And Source Truth

This capability owns application-level duplicate-effect prevention: idempotency key scope, request fingerprint, dedupe state, replay semantics, retry policy, timeout/unknown-outcome recovery, terminal failure, DLQ/replay ownership, and validation evidence. It does not own broker topology, job lifecycle, transaction isolation, public API schema, or provider-specific protocol details except as handoff boundaries.

Source truth is current handlers, services, consumers, external-write adapters, idempotency stores, queue/job config, retry wrappers, tests, runbooks, dashboards, registry/routing entries, and final validation output. Repository graph, project memory, generated reports, previous incidents, and earlier validation are selectors only until current source inspection and post-edit validation confirm them.

# Stage Fit

- **Planning:** use when a write, submit, external call, webhook, queue consumer, or replay path can execute more than once and the safe duplicate behavior is not yet explicit.
- **Coding / bug-fix / debugging / code-review / refactoring:** verify key generation point, caller binding, payload hash, in-flight state, atomic dedupe/side-effect ordering, retry classification, circuit interaction, and terminal state before changing helpers, adapters, consumers, or retry wrappers.
- **Testing / validation:** map duplicate request, same-key payload mismatch, in-flight duplicate, timeout recovery, retry exhaustion, DLQ/replay, and cross-caller replay to executable or explicitly not-run evidence.
- **Release / operations:** require retry-rate, duplicate-detected, idempotency-store-error, DLQ depth, replay, reconciliation, and circuit-state signals with owners and rollback or stop criteria.
- **Graph / memory / execution coupling:** treat graph, memory, runbook, incident, and old report claims as leads; reconcile them against current source, final command order, and validation freshness before closure.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| Synchronous command/write | POST/PATCH/create/submit/pay/refund/order with client retry or timeout. | Operation key, fingerprint, in-flight and committed replay, unknown outcome. | Header/key source, payload hash, dedupe store, duplicate and timeout tests. | `api-contract-design`, `controller-api-implementation` | Skip for read-only GET or naturally idempotent PUT with no side effect. |
| External write/reconciliation | Payment, email/SMS, CRM, fulfillment, provider write, or non-idempotent SDK call. | Provider reference, retry budget, reconciliation-before-retry, terminal recovery. | Provider idempotency support, reference lookup, retryable errors, reconciliation test. | `integration-change-builder`, `reliability-observability-gate` | Skip provider depth when no external side effect exists. |
| Queue/webhook consumer | At-least-once delivery, webhook replay, DLQ replay, visibility timeout, redelivery. | Inbox/dedupe, message id/key, ack/commit timing, replay safety. | Dedupe store, ack point, duplicate delivery test, DLQ/replay runbook. | `message-queue-design`, `async-job-design` | Skip broker topology unless partitions, offsets, or DLQ config changed. |
| Retry policy safety | Timeout, 429, 503, SDK retry, circuit breaker, cancellation, partial failure. | Bounded attempts, full jitter, retryable/non-retryable split, circuit interaction. | Max attempts/deadline, backoff formula, retry budget, terminal-state proof. | `degradation-circuit-breaking`, `failure-contract-design` | Skip retries for permanent validation/authz errors. |
| Evidence freshness | Prior graph, memory, report, incident note, or validation claims this path is safe. | Confirm current source and final validation rather than reusing stale proof. | Inspected paths, accepted/rejected memory, command order, freshness verdict. | `repository-graph-analysis`, `project-memory-governance`, `validation-broker` | Skip only for wording-only edits with no safety claim. |

# Selection Rules

Select this capability when **duplicate effect prevention and bounded retry policy** are the primary design concern. Adjacent routing:

- Prefer `async-job-design` when the primary concern is job worker lifecycle (scheduling, concurrency, job state management).
- Prefer `event-driven-architecture` when the primary concern is broker-level delivery guarantees and consumer group design.
- Prefer `form-validation-design` when the primary concern is client-side duplicate-submit protection (button disable + idempotency key generation).
- Prefer `integration-change-builder` when the primary concern is third-party API protocol and error handling.
- Prefer `transaction-consistency` when the primary concern is distributed transaction coordination and compensation.

# Proactive Professional Triggers

- **Signal:** A POST/PATCH/create/pay/refund/submit path allows caller retry or browser refresh without a stable operation-level key. **Hidden risk:** the retry creates a second committed side effect while appearing like normal recovery. **Required professional action:** require key generation at operation initiation, caller/tenant binding, payload hash, and duplicate replay behavior. **Route to:** `api-contract-design`, `quality-test-gate`. **Evidence required:** key source, scope, duplicate request test, same-key-different-payload test.
- **Signal:** Timeout, cancellation, or network failure is treated as ordinary failure and retried automatically. **Hidden risk:** the first attempt may have committed while the response was lost. **Required professional action:** classify unknown outcome, reconcile by idempotency key or provider reference before retry, and define the safe user/operator response. **Route to:** `failure-contract-design`, `integration-change-builder`. **Evidence required:** timeout state, reconciliation query, retry/no-retry decision, unknown-outcome test.
- **Signal:** Queue, webhook, scheduled job, or DLQ replay handler performs payment, notification, inventory, entitlement, ledger, or external writes without durable dedupe. **Hidden risk:** redelivery or replay repeats irreversible work. **Required professional action:** define message/operation id, inbox or idempotency store, ack timing, replay policy, and terminal owner. **Route to:** `message-queue-design`, `async-job-design`. **Evidence required:** dedupe key, ack/commit point, duplicate-delivery test, DLQ replay proof or residual risk.
- **Signal:** Retry policy says "retry 5xx" or uses SDK defaults without max elapsed time, jitter, retry budget, circuit interaction, or non-retryable errors. **Hidden risk:** retry storms overload a degraded dependency and duplicate unsafe writes. **Required professional action:** bound attempts, total deadline, full jitter, retryable list, non-retryable list, circuit state, and terminal path. **Route to:** `degradation-circuit-breaking`, `reliability-observability-gate`. **Evidence required:** retry matrix, backoff formula, load amplification limit, terminal-state validation.
- **Signal:** Project memory, repository graph, old incident notes, generated report, or previous validation says idempotency is already handled. **Hidden risk:** stale topology hides a new caller, adapter, retry wrapper, consumer, or validation gap. **Required professional action:** inspect current source, compare same-pattern side-effect paths, rerun mapped validators, and state what remains unverified. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, `validation-broker`. **Evidence required:** inspected paths, accepted/rejected prior claim, command freshness, residual duplicate-effect risk.

# Risk Escalation Rules

Escalate when: an operation moves money (payment capture, refund, transfer); creates a binding commercial record (order, booking, contract); sends a legally required notification (regulatory disclosure, GDPR notice); modifies inventory that could cause oversell; or runs in a distributed system where the operation crosses multiple service or database boundaries without a shared transaction.

# Critical Details

The most dangerous failure in idempotency design is quiet: a duplicate operation that produces a plausible-looking result with no visible anomaly until a reconciliation audit finds the discrepancy. Precision failures:

- **Payload mismatch accepted silently.** Idempotency key `key-abc123` was used for a $100 charge. Due to a bug, the retry sends `key-abc123` with a $200 payload. The server checks only the key; finds it processed; returns the cached $100 response. The caller believes the $200 charge succeeded. Reconciliation later finds no $200 charge. Fix: `payload_hash` must be part of the idempotency check. Mismatch = 422 error.
- **Key generated per retry, not per operation.** Client generates a new UUID on every request attempt. Each retry is treated as a new operation. 3 retries = 3 payment charges. Fix: generate UUID once at operation initiation; use the same key on all retries.
- **Key not bound to caller.** Client A generates `key-xyz`. Client B replays the same `key-xyz` with their own payload. Server matches key; returns Client A's cached result. Cross-client replay attack. Fix: idempotency key must be bound to the authenticated caller identity (`userId` or `apiClientId`).
- **Retry of unknown timeout outcome.** Payment capture times out after 10s. Client retries with same idempotency key. But in the 10s window, the bank processed the charge and the network failed returning the response. Server finds `key` already committed → returns cached success → correct. Without idempotency key → second charge created. Idempotency key is the only correct mechanism for timeout recovery on mutations.
- **Infinite retry storm.** A dependency returns 503. The consumer retries aggressively: 1000 RPS retries. The dependency is further overloaded. Recovery time doubles. Circuit breaker + retry budget (max 10% additional load from retries) prevents retry storms. **Polly** (C#), **Resilience4j** (Java), **tenacity** (Python), **axios-retry** (JavaScript) implement both circuit breaker and retry budget.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| New UUID per retry attempt | Every retry is a new operation; N retries = N side effects |
| Idempotency key with no payload hash check | Payload mismatch silently processes wrong amount |
| Key not bound to caller identity | Cross-caller key replay; wrong operation replayed |
| Retry 400 Bad Request | Permanent client error; infinite loop; never resolves |
| Idempotency key TTL = 1 hour, retry deadline = 24h | Keys expire before retry window; re-processing vulnerability |
| No DLQ; discard on max retries | Silent data loss; no alert; no operator recovery |
| Retry on 409 Conflict as transient error | 409 means already processed; check idempotency store; return cached |
| No circuit breaker on retry | Retry storm when dependency down; cascading failure |

# Failure Modes

- **New UUID per retry:** New UUID per payment retry: 3 retries = 3 charges; customer charged $300 instead of $100; refund required; P0 incident.
- **Payload mismatch accepted:** Payload mismatch accepted: $200 charge replayed with $500 payload; cached $200 returned; ledger shows $200; bank processed $500; financial discrepancy.
- **Expired key reprocesses:** Idempotency key expiry before retry: key expires in 1 hour; retry at hour 2; new charge created; duplicate.
- **Retry storm:** Retry on 503 with no circuit breaker: 1000 RPS retry storm; dependency overloaded; recovery time 3x longer; cascading failure.
- **Silent webhook drop:** Webhook max retries exhausted; silently discarded; no DLQ; consuming service never receives event; order stuck in "pending" state forever.
- **Unknown timeout duplicate:** Timeout recovery without idempotency key: payment committed server-side; response lost; retry creates second charge; customer dispute.
- **Cross-caller replay:** Key not bound to caller: API key leaked; attacker replays idempotency keys; injects payment results for other merchants.
- **Missing dead-letter table:** No dead-letter table: background job fails 5 times; silently dropped; 10,000 invoices not generated; discovered in monthly billing reconciliation.

# Reference Loading Policy

Use the `SKILL.md` body for L1/L2 routing, stage fit, mode selection, triggers, output contract, evidence, and quality gates. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete idempotency/retry design for payments, subscriptions, orders, webhooks, queue consumers, retries, redelivery, scheduled jobs, external writes, or harmful duplicate side effects. Load [references/evidence-patterns.md](references/evidence-patterns.md) only when the handoff needs source-to-validation mapping, graph/memory/execution freshness, tool permission boundary, replay/reconciliation evidence, or residual-risk wording. Load [references/industry-benchmarks.md](references/industry-benchmarks.md) when release evidence, audit, high-risk provider behavior, retry-budget math, outbox/inbox, or named benchmark support is required. Use [examples/example-output.md](examples/example-output.md) only when the final output shape is unclear. Do not load deep references for read-only retry wrappers or local-only retries with no external side effect.

# Output Contract

Return an idempotency and retry contract with:

- `mode_selected` with trigger signal and skipped adjacent capabilities.
- `source_evidence` (current handlers, services, consumers, adapters, stores, tests, runbooks, dashboards, graph/memory/report claims accepted or rejected).
- `operations` (name, operation type, side effects, idempotency required?)
- `idempotency_key` (generation point, scope: key+caller+operation+payload_hash, retention window)
- `key_storage` (database table, inbox table, Redis, or provider key; schema; TTL; persistence guarantee; unique index)
- `payload_mismatch` (detection method; response: 422; logging)
- `state_machine` (processing, committed, failed, expired, replayed, terminal, and safe transitions)
- `on_duplicate` (key found committed: return cached response; key found in-flight: 409 + Retry-After; expired key behavior)
- `retry_policy` (max attempts, deadline, backoff algorithm, jitter config, retryable errors, non-retryable errors)
- `circuit_breaker` (failure threshold, open duration, half-open probe, retry budget)
- `terminal_state` (DLQ destination, alert threshold, operator runbook, reconciliation procedure)
- `reconciliation` (for timeout scenarios: lookup by idempotency key or reference ID before retry)
- `observability` (metrics: attempt count, retry rate, duplicate detection rate, idempotency-store errors, DLQ depth, replay count, circuit state)
- `graph_memory_execution_coupling` (current graph/memory/trajectory/report facts used, rejected, stale, not verified, and final validation order)
- `tool_permission_boundary` (read-only vs state-mutating validation/replay/provider actions, sandbox, rollback, redaction)
- `tests` (duplicate key, payload mismatch, in-flight duplicate, timeout recovery, cross-caller replay, expired key, retry exhaustion, DLQ/replay, circuit breaker)

# Evidence Contract

An idempotency/retry design is complete only when the output includes:

- **Operation identity**: operation name, side effect, resource boundary, tenant/user scope, and external dependency.
- **Current evidence**: source paths, registry/routing entries, graph slice, memory signals, tests, runbooks, dashboards, and validation order inspected or explicitly skipped.
- **Idempotency key source**: client key, server-generated key, message ID, natural key, or composite key.
- **Request fingerprint**: behavior when the same idempotency key is reused with a different payload.
- **In-flight behavior**: behavior when the same key arrives while the first request is still processing.
- **Key scope**: tenant/user/resource/time-window uniqueness and collision behavior.
- **Dedupe store**: storage location, unique index, TTL, cleanup, and failure behavior.
- **Atomicity**: whether dedupe record creation and side effect commit are atomic; if not, how partial success is recovered.
- **Replay behavior**: original response replay, in-progress response, expired-key behavior, and conflict response.
- **Retry policy**: retryable errors, non-retryable errors, backoff, jitter, max attempts, and timeout.
- **Poison message / DLQ policy**: when retry stops, where the message goes, and how operators replay safely.
- **Graph / memory / execution freshness**: prior claims accepted, rejected, stale, or not verified, and validators run after the final material edit.
- **Tool boundary**: whether replay, provider, queue, database, cache, validation, or diagnostic actions are read-only or state-mutating, with rollback and redaction.
- **Validation evidence**: duplicate request test, same-key-different-payload test, in-flight request test, expired key test, retry exhaustion test, and DLQ/replay test.
- **What evidence proves**: the protected duplicate/retry path.
- **What evidence does not prove**: untested downstream idempotency, production race, external system behavior, or clock skew.
- **Residual risk**: side effects still not idempotent, owner, and next gate.

# Quality Gate

The idempotency and retry design is complete only when:

1. Idempotency key generation point is client-side at operation initiation (not per-retry).
2. Idempotency check includes payload hash; mismatch returns 422 with explanation.
3. Key bound to authenticated caller identity; cross-caller reuse rejected.
4. Key retention window > max retry deadline (minimum 7 days recommended).
5. Retry policy bounded: max attempts, deadline, backoff with full jitter, retryable error list.
6. Non-retryable errors enumerated: 400, 401, 403, 409, 422 — not retried.
7. Circuit breaker defined for every external dependency that is retried.
8. Terminal state: DLQ with alert, operator runbook, and reconciliation procedure.
9. Timeout scenario handled: reconciliation query before retry for unknown-outcome mutations.
10. Tests cover: duplicate submission, payload mismatch, cross-caller replay, circuit breaker open, DLQ routing.
11. In-flight duplicate, expired key, retry exhaustion, and replay behavior are defined or marked non-applicable with evidence.
12. Current source, graph, memory, reports, and prior validation are reconciled; stale evidence cannot support closure.
13. Validation freshness is stated after the final material edit, with not-run or partial checks labeled honestly.
14. Tool permission/sandbox boundary is recorded for replay, provider, queue, database, cache, validation, build, install, or diagnostic actions.

# Benchmark Coverage

This capability covers HTTP/API idempotency keys, caller-bound request fingerprints, durable dedupe stores, inbox/outbox retry safety, bounded retry with full jitter, retry budget and circuit interaction, timeout unknown-outcome reconciliation, DLQ/replay terminal states, duplicate-delivery validation, graph-memory-execution freshness, and tool-boundary evidence. It does not prove broker topology, provider-side guarantees, job lifecycle, transaction isolation, or production readiness without the companion gates selected above.

# Routing Coverage

Routes from `backend-change-builder`, `integration-change-builder`, `reliability-observability-gate`, `api-contract-design`, `message-queue-design`, `async-job-design`, `transaction-consistency`, `degradation-circuit-breaking`, `failure-contract-design`, and `change-forge-router` should arrive here when duplicate side effects and bounded retries are the primary decision. Route away when the primary issue is broker partitioning, durable job status, transaction boundary, provider-specific authentication, public error taxonomy, release rollout, or observability implementation.

# Used By

- backend-change-builder
- integration-change-builder
- reliability-observability-gate

# Handoff

Hand off to `async-job-design` for worker processing lifecycle; `event-driven-architecture` for broker-level delivery guarantees and DLQ; `controller-api-implementation` for `Idempotency-Key` header handling in the API layer; `reliability-observability-gate` for production retry rate and DLQ depth alerting.

# Completion Criteria

The capability is complete when **retrying or redelivering any covered operation cannot silently create duplicate side effects, every retry path has a bounded terminal state, and every permanent failure is routed to an owned DLQ with an alert and a reconciliation procedure**.
