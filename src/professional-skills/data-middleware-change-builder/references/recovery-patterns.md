# Data Middleware Recovery Patterns

Use this reference for changes where failure recovery, replay, rollback, reconciliation, or release watch is material to correctness. Recovery design must name the owner, trigger, bounded action, and stop condition.

## Recovery Patterns
- **Source-of-truth drift:** define the authoritative store, reconciliation query, repair direction, sampling or full-scan strategy, alert threshold, and audit trail.
- **Cache stale or stampede failure:** define explicit invalidation, TTL fallback, single-flight or lock behavior, origin backpressure, cache-down mode, and freshness metric.
- **Queue duplicate or poison message:** define idempotency key, dedupe store, ack/commit boundary, DLQ metadata, replay command, retry budget, and terminal failure handling.
- **Migration or backfill failure:** define pause/resume, chunk size, lock timeout, rollback migration, partial-state detector, compatibility window, and cleanup step.
- **Search or derived index failure:** define shadow index, replay source, alias rollback, missing-document detector, index freshness metric, and customer-impact boundary.

## Release Watch
- Name the metrics, logs, traces, reports, or dashboards that prove recovery is working during rollout.
- Define rollback thresholds before release: lock wait, query latency, cache miss storm, queue lag, DLQ depth, reconciliation drift, error rate, and cost spike.
- Hand unresolved capacity, alert, dashboard, or incident-readiness gaps to `reliability-observability-gate` or `delivery-release-gate` with owner and residual risk.

