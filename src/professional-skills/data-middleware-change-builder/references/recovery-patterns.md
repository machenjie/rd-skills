# Data Middleware Recovery Patterns

Load when failure recovery, replay, rollback, reconciliation, or release watch is material. For the selected failure window, name owner, trigger, bounded action, and stop condition; disclose irreversible or provider-owned steps.

## Recovery Patterns
- **Source-of-truth drift:** authoritative store; reconciliation query and direction; sample/full scan; threshold; audit trail.
- **Cache stale/stampede:** invalidation; TTL fallback; single-flight/lock; origin backpressure; cache-down mode; freshness metric.
- **Queue duplicate/poison:** idempotency key; dedupe store; ack/commit boundary; DLQ metadata; replay command; retry budget; terminal handling.
- **Migration/backfill:** pause/resume; chunk size; lock timeout; rollback migration; partial-state detector; compatibility window; cleanup.
- **Search/derived index:** shadow index; replay source; alias rollback; missing-document detector; freshness metric; impact boundary.

## Release Watch
- **Evidence:** rollout metrics, logs, traces, reports, or dashboards that prove recovery.
- **Pre-release rollback thresholds:** lock wait, query latency, miss storm, queue lag, DLQ depth, drift, errors, and cost.
- **Capability boundary:** unresolved capacity, alert, dashboard, incident-readiness, or release-approval gaps remain outside data/middleware authority; record their owner and residual risk.
