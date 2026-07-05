# Idempotency Retry Industry Benchmarks

Load this reference only when release evidence, audit, or high-risk payment/webhook/queue retry behavior needs named benchmark support.

## Benchmark Anchors

Anchor against: **Stripe Idempotency Keys** - `Idempotency-Key` header on every POST; 30-day key retention; 422 on payload mismatch; cached response on duplicate; documented at stripe.com/docs/api/idempotent_requests. **IETF draft-ietf-httpapi-idempotency-key-header** - standardization of `Idempotency-Key` header across HTTP APIs. **Transactional Outbox Pattern** (Richardson, 2018; Kleppmann DDIA) - write operation + outbox event in same database transaction; separate relay reads outbox and delivers; ensures at-least-once delivery without dual write. **Inbox Pattern** (Transactional Inbox) - consumer writes message ID to inbox table in same transaction as processing; duplicate delivery check via inbox before processing. **Exponential Backoff with Full Jitter** (AWS Architecture Blog, 2015) - `sleep = random_between(0, min(cap, base * 2^attempt))`; full jitter eliminates synchronization between retrying clients; `cap` prevents unbounded delay. **Google SRE Book** (Beyer et al.) - Ch. 22 Cascade Failures: retry storms; retry budgets (10% additional load from retries); circuit breakers to stop retries when dependency is down. **RFC 7231** - HTTP/1.1 Semantics: idempotent methods (GET, PUT, DELETE, HEAD, OPTIONS, TRACE); POST is NOT idempotent by definition. **AWS SQS Visibility Timeout** - implicit retry mechanism; message reappears after visibility timeout if not deleted; requires consumer idempotency. **Kafka EOS (Exactly-Once Semantics)** - idempotent producer (no duplicates on retry); transactional API for atomic produce + consumer-offset commit; does NOT cover external side effects. **Saga Pattern (Richardson)** - compensation transactions for at-least-once distributed transaction rollback; must also be idempotent. **Redis + SET NX EX** - `SET idempotency:{key} {result} NX EX 604800` - atomic check-and-set; 7-day TTL; used for fast idempotency store. **PostgreSQL `ON CONFLICT DO NOTHING`** - database-level deduplication for idempotency key store; `INSERT INTO idempotency_keys (key, result, created_at) VALUES (...) ON CONFLICT (key) DO NOTHING RETURNING *`.

## Idempotency Key Design Matrix

| Dimension | Decision | Anti-pattern |
| --- | --- | --- |
| Key generation | Client generates UUID v4 at operation initiation (not at retry) | Server generates key - breaks idempotency guarantee |
| Key scope | Per operation type + operation payload hash | One key used for all operations by the same client |
| Payload mismatch | Reject with 422; return error explaining mismatch | Silently process new payload - silent corruption |
| Key retention | Max(retry_deadline, 7 days) minimum | TTL < retry window - re-processing vulnerability |
| Key storage | Idempotency key table in same database as operation; OR Redis with persistence | In-memory only - lost on restart; or external service that can fail |
| On duplicate (key found, committed) | Return cached response (200 or original status) | Re-process - duplicate side effect |
| On duplicate (key found, in-flight) | Return 409 Conflict with Retry-After | Return 200 pretending to succeed |
| Key binding to caller | Key must be bound to authenticated caller (userId or clientId) - reject cross-caller reuse | Any caller can use any key - replay attack vector |

## Retry Policy Configuration

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

## Idempotency Store Implementation

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
-- If no row returned: duplicate -> query existing row -> return cached response
-- If row returned: proceed with operation -> UPDATE status/response on completion
```
