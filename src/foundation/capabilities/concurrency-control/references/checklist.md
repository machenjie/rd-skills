# Concurrency Control Checklist

- Map each shared resource to actors, invariant, current source path, transaction/queue boundary, and overlapping execution scenario.
- Choose the narrowest control: atomic statement, optimistic version, row lock, unique constraint, compare-and-swap, queue partition, idempotency store, lease, or fencing token.
- Record rejected mechanisms and why they were too broad, too weak, too slow, or owned by another capability.
- Define conflict detection, retry/backoff, timeout, terminal outcome, and caller-facing response for every actor.
- Verify duplicate-submit and worker-redelivery behavior with durable idempotency storage and payload-fingerprint handling.
- Analyze lock ordering, lock duration, lock-across-I/O risk, deadlock path, hot row/partition risk, and contention metric.
- Confirm distributed leases have TTL, release, refresh/stop behavior, monotonic fencing token, and stale-token rejection.
- Prove event-publish safety through outbox/post-commit behavior; reject publish-before-commit.
- Add deterministic parallel, stress, race-detector, or redelivery tests for high-risk paths; name command, output, exit code, and artifact/report.
- Close with graph/memory/trajectory judgment, changed-concurrency-to-validation map, residual risks, evidence limits, and next gate.
