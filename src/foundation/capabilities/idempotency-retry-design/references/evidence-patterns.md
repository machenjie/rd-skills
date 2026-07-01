# Idempotency Retry Evidence Patterns

## Required Evidence

- Source boundary: handlers, services, consumers, external-write adapters, retry wrappers, idempotency stores, queue/job config, tests, runbooks, dashboards, and owner.
- Operation evidence: side effect, tenant/user/resource scope, key source, operation type, payload hash, caller binding, retention window, and collision behavior.
- Dedupe/atomicity evidence: unique index or inbox/outbox record, in-flight behavior, commit ordering, stored response, expired-key behavior, and partial-success recovery.
- Retry evidence: retryable and non-retryable error classes, max attempts, total deadline, full-jitter formula, retry budget, circuit breaker state, and terminal state.
- Replay/reconciliation evidence: provider reference lookup, timeout unknown-outcome decision, DLQ destination, replay runbook, alert owner, and compensation boundary.
- Graph/memory/execution evidence: inspected paths, same-pattern side-effect scan, accepted/rejected prior claims, final validation order, and what remains unknown.

## Tool Permission Boundary

Classify actions as read-only inspection, local validation/report write, replay dry run, queue/database/cache test-data write, provider/network lookup, migration/backfill action, or live replay/reconciliation. State sandbox/approval state, write scope (`HOME`, source tree, report artifacts, `dist/`, local DB/queue, provider sandbox, production), rollback path, and secret/PII redaction rule.

## Handoff Shape

```markdown
Idempotency Retry Evidence Record
- Source boundary:
- Operation identity proof:
- Dedupe and atomicity proof:
- Retry/circuit proof:
- Replay/reconciliation proof:
- Graph/memory/execution freshness:
- Tool permission boundary:
- Validation:
- What remains unproved:
- Residual duplicate-effect risk:
```

## Blocking Conditions

Block completion when a mutation can retry without an operation-level key, same-key payload mismatch behavior is undefined, dedupe and side effect ordering is not mapped, retry exhaustion lacks an owned terminal state, stale memory is reused without same-pattern source confirmation, or replay/provider/database actions lack write-scope and rollback disclosure.
