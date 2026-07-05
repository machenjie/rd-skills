# Idempotency Retry Design Checklist

- Identify every side effect and duplicate-execution risk.
- Define idempotency key source, scope, operation, subject, and retention window.
- Compare payloads for repeated keys and define conflict behavior.
- Store original outcome or enough state to replay safely.
- Classify retryable, non-retryable, timeout, and unknown-outcome errors.
- Set max attempts, total deadline, backoff, jitter, and retry budget.
- Prevent retries of unsafe mutations without idempotency.
- Define deduplication for webhooks, async consumers, and external callbacks.
- Define terminal failure, compensation, reconciliation, or manual recovery.
- Reconcile repository graph, project memory, runbooks, old reports, and prior validation against current source.
- Record read-only versus state-mutating replay, provider, queue, database, cache, validation, and diagnostic actions.
- Add tests for duplicate request, timeout retry, conflict payload, permanent failure, and replay.
