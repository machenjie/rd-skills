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

Anchor against: **Stripe Idempotency Keys** — `Idempotency-Key` header on every POST; 30-day key retention; 422 on payload mismatch; cached response on duplicate; documented at stripe.com/docs/api/idempotent_requests. **IETF draft-ietf-httpapi-idempotency-key-header** — standardization of `Idempotency-Key` header across HTTP APIs. **Transactional Outbox Pattern** (Richardson, 2018; Kleppmann DDIA) — write operation + outbox event in same database transaction; separate relay reads outbox and delivers; ensures at-least-once delivery without dual write. **Inbox Pattern** (Transactional Inbox) — consumer writes message ID to inbox table in same transaction as processing; duplicate delivery check via inbox before processing. **Exponential Backoff with Full Jitter** (AWS Architecture Blog, 2015) — `sleep = random_between(0, min(cap, base * 2^attempt))`; full jitter eliminates synchronization between retrying clients; `cap` prevents unbounded delay. **Google SRE Book** (Beyer et al.) — Ch. 22 Cascade Failures: retry storms; retry budgets (10% additional load from retries); circuit breakers to stop retries when dependency is down. **RFC 7231** — HTTP/1.1 Semantics: idempotent methods (GET, PUT, DELETE, HEAD, OPTIONS, TRACE); POST is NOT idempotent by definition. **AWS SQS Visibility Timeout** — implicit retry mechanism; message reappears after visibility timeout if not deleted; requires consumer idempotency. **Kafka EOS (Exactly-Once Semantics)** — idempotent producer (no duplicates on retry); transactional API for atomic produce + consumer-offset commit; does NOT cover external side effects. **Saga Pattern (Richardson)** — compensation transactions for at-least-once distributed transaction rollback; must also be idempotent. **Redis + SET NX EX** — `SET idempotency:{key} {result} NX EX 604800` — atomic check-and-set; 7-day TTL; used for fast idempotency store. **PostgreSQL `ON CONFLICT DO NOTHING`** — database-level deduplication for idempotency key store; `INSERT INTO idempotency_keys (key, result, created_at) VALUES (...) ON CONFLICT (key) DO NOTHING RETURNING *`.

### Idempotency Key Design Matrix

| Dimension | Decision | Anti-pattern |
| --- | --- | --- |
| Key generation | Client generates UUID v4 at operation initiation (not at retry) | Server generates key — breaks idempotency guarantee |
| Key scope | Per operation type + operation payload hash | One key used for all operations by the same client |
| Payload mismatch | Reject with 422; return error explaining mismatch | Silently process new payload — silent corruption |
| Key retention | Max(retry_deadline, 7 days) minimum | TTL < retry window — re-processing vulnerability |
| Key storage | Idempotency key table in same database as operation; OR Redis with persistence | In-memory only — lost on restart; or external service that can fail |
| On duplicate (key found, committed) | Return cached response (200 or original status) | Re-process — duplicate side effect |
| On duplicate (key found, in-flight) | Return 409 Conflict with Retry-After | Return 200 pretending to succeed |
| Key binding to caller | Key must be bound to authenticated caller (userId or clientId) — reject cross-caller reuse | Any caller can use any key — replay attack vector |

### Retry Policy Configuration

```
Exponential backoff with full jitter:
  attempt:  0    1    2    3    4    5
  base:     1s
  cap:      30s
  formula:  sleep = random(0, min(cap, base * 2^attempt))
  delays:   0-1s, 0-2s, 0-4s, 0-8s, 0-16s, 0-30s

Recommended per operation class:
  Payment capture:
    max_attempts: 3
    deadline: 5 minutes
    backoff: full jitter, cap 60s
    retryable: network error, 429, 503
    non-retryable: 400, 401, 403, 409, 422 (check idempotency store on 409)
    terminal: DLQ + alert + reconciliation

  External API write (e.g., CRM update, email send):
    max_attempts: 5
    deadline: 15 minutes
    backoff: full jitter, cap 30s
    retryable: network error, 429, 503, 500
    non-retryable: 400, 401, 403, 422

  Webhook delivery to external party:
    max_attempts: 15 over 72 hours (Stripe-style progressive)
    schedule: 5s, 30s, 2min, 10min, 1h, 4h, 8h, 12h, ...
    retryable: network error, 429, 5xx
    non-retryable: 200-299 (success), 410 Gone (endpoint removed)
    terminal: DLQ + notify event producer

  Async consumer (Kafka/SQS message):
    max_attempts: 5
    backoff: full jitter per attempt
    terminal: route to DLQ topic/queue; do not commit offset / do not delete message
```

### Idempotency Store Implementation

```sql
-- PostgreSQL idempotency key table
CREATE TABLE idempotency_keys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key             VARCHAR(255) NOT NULL,
    caller_id       VARCHAR(255) NOT NULL,         -- bound to authenticated caller
    operation_type  VARCHAR(100) NOT NULL,
    payload_hash    CHAR(64)     NOT NULL,          -- SHA-256 of canonical payload
    status          VARCHAR(20)  NOT NULL DEFAULT 'processing', -- processing|committed|failed
    response_status INTEGER,
    response_body   JSONB,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ  NOT NULL,          -- now() + 7 days
    CONSTRAINT uq_key_caller UNIQUE (key, caller_id)
);

-- Check before processing:
INSERT INTO idempotency_keys (key, caller_id, operation_type, payload_hash, status, expires_at)
VALUES ($1, $2, $3, $4, 'processing', now() + interval '7 days')
ON CONFLICT (key, caller_id) DO NOTHING
RETURNING id;
-- If no row returned: duplicate → query existing row → return cached response
-- If row returned: proceed with operation → UPDATE status/response on completion
```

# Selection Rules

Select this capability when **duplicate effect prevention and bounded retry policy** are the primary design concern. Adjacent routing:

- Prefer `async-job-design` when the primary concern is job worker lifecycle (scheduling, concurrency, job state management).
- Prefer `event-driven-architecture` when the primary concern is broker-level delivery guarantees and consumer group design.
- Prefer `form-validation-design` when the primary concern is client-side duplicate-submit protection (button disable + idempotency key generation).
- Prefer `integration-change-builder` when the primary concern is third-party API protocol and error handling.
- Prefer `transaction-consistency` when the primary concern is distributed transaction coordination and compensation.

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

- New UUID per payment retry: 3 retries = 3 charges; customer charged $300 instead of $100; refund required; P0 incident.
- Payload mismatch accepted: $200 charge replayed with $500 payload; cached $200 returned; ledger shows $200; bank processed $500; financial discrepancy.
- Idempotency key expiry before retry: key expires in 1 hour; retry at hour 2; new charge created; duplicate.
- Retry on 503 with no circuit breaker: 1000 RPS retry storm; dependency overloaded; recovery time 3x longer; cascading failure.
- Webhook max retries exhausted; silently discarded; no DLQ; consuming service never receives event; order stuck in "pending" state forever.
- Timeout recovery without idempotency key: payment committed server-side; response lost; retry creates second charge; customer dispute.
- Key not bound to caller: API key leaked; attacker replays idempotency keys; injects payment results for other merchants.
- No dead-letter table: background job fails 5 times; silently dropped; 10,000 invoices not generated; discovered in monthly billing reconciliation.

# Reference Loading Policy

Read `references/checklist.md` only when the change touches payments, subscriptions, orders, webhooks, queue consumers, retries, redelivery, scheduled jobs, external writes, or operations where duplicate side effects are harmful. Do not load deep references for read-only retry wrappers or local-only retries with no external side effect.

# Output Contract

Return an idempotency and retry contract with:

- `operations` (name, operation type, side effects, idempotency required?)
- `idempotency_key` (generation point, scope: key+caller+operation+payload_hash, retention window)
- `key_storage` (database table or Redis; schema; TTL; persistence guarantee)
- `payload_mismatch` (detection method; response: 422; logging)
- `on_duplicate` (key found committed: return cached response; key found in-flight: 409 + Retry-After)
- `retry_policy` (max attempts, deadline, backoff algorithm, jitter config, retryable errors, non-retryable errors)
- `circuit_breaker` (failure threshold, open duration, half-open probe, retry budget)
- `terminal_state` (DLQ destination, alert threshold, operator runbook, reconciliation procedure)
- `reconciliation` (for timeout scenarios: lookup by idempotency key or reference ID before retry)
- `observability` (metrics: attempt count, retry rate, DLQ depth, duplicate detection rate, circuit state)
- `tests` (duplicate key test, payload mismatch test, timeout recovery test, cross-caller replay test, DLQ routing test, circuit breaker test)

# Evidence Contract

An idempotency/retry design is complete only when the output includes:

- **Operation identity**: operation name, side effect, resource boundary, tenant/user scope, and external dependency.
- **Idempotency key source**: client key, server-generated key, message ID, natural key, or composite key.
- **Request fingerprint**: behavior when the same idempotency key is reused with a different payload.
- **In-flight behavior**: behavior when the same key arrives while the first request is still processing.
- **Key scope**: tenant/user/resource/time-window uniqueness and collision behavior.
- **Dedupe store**: storage location, unique index, TTL, cleanup, and failure behavior.
- **Atomicity**: whether dedupe record creation and side effect commit are atomic; if not, how partial success is recovered.
- **Replay behavior**: original response replay, in-progress response, expired-key behavior, and conflict response.
- **Retry policy**: retryable errors, non-retryable errors, backoff, jitter, max attempts, and timeout.
- **Poison message / DLQ policy**: when retry stops, where the message goes, and how operators replay safely.
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

# Used By

- backend-change-builder
- integration-change-builder
- reliability-observability-gate

# Handoff

Hand off to `async-job-design` for worker processing lifecycle; `event-driven-architecture` for broker-level delivery guarantees and DLQ; `controller-api-implementation` for `Idempotency-Key` header handling in the API layer; `reliability-observability-gate` for production retry rate and DLQ depth alerting.

# Completion Criteria

The capability is complete when **retrying or redelivering any covered operation cannot silently create duplicate side effects, every retry path has a bounded terminal state, and every permanent failure is routed to an owned DLQ with an alert and a reconciliation procedure**.
