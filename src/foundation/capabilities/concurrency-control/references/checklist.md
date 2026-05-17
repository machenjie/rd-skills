# Concurrency Control Checklist

- Identify shared resource, actors, invariant, and overlapping execution scenarios.
- Choose lock, version, unique constraint, lease, idempotency, queue partition, or compare-and-swap.
- Define conflict detection, retry behavior, timeout, and terminal outcome.
- Analyze deadlocks, lock ordering, lock duration, and contention impact.
- Handle duplicate submits and duplicate worker execution.
- Add parallel, stress, or deterministic race tests for high-risk paths.
