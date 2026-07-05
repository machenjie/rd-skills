# Async Job Design Checklist

- Define job name, trigger, owner, and expected outcome.
- Use stable identifiers in payload and document any intentional snapshot semantics.
- Define idempotency key and duplicate-delivery behavior.
- Define execution steps, ordering, and transaction boundaries.
- Set timeout, max attempts, backoff, jitter, and terminal states.
- Classify transient, permanent, cancelled, and unknown-outcome failures.
- Define status visibility for users, operators, or dependent systems.
- Define cancellation behavior and compensation for committed side effects.
- Add logs, metrics, traces, correlation ids, and dead-letter or failure queues.
- Add tests for success, duplicate delivery, retry, timeout, cancellation, and partial failure.
