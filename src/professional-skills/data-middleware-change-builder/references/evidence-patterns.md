# Data Middleware Evidence Patterns

Use this reference when a data or middleware plan needs proof beyond an unverified code-reading judgment. Keep evidence proportional to risk. Load only the rows, plans, logs, metrics, or reports needed to prove the claim.

## Evidence Map
- **Query or index change:** capture the validator or command, representative dataset size, `EXPLAIN` or plan output artifact, exit code, latency/cardinality judgment, and whether production distribution is still assumed.
- **Cache change:** prove key shape, tenant isolation, TTL, invalidation, stampede control, cache-down fallback, and stale-read behavior with deterministic tests or bounded integration evidence.
- **Queue or stream change:** prove delivery semantics, offset/ack timing, duplicate handling, retry/backoff, poison-message routing, DLQ alerting, replay safety, and ordering limits.
- **Migration or backfill:** prove forward path, rollback path, lock behavior, batching, resumability, reconciliation, execution window, and release watch signals.
- **Search or derived store:** prove shadow index or blue/green cutover, mapping compatibility, replay or reindex progress, alias switch rollback, and drift reconciliation.

## Evidence Rules
- For executable or report-backed claims, record the validator, artifact, status, dataset freshness, and exact claim; for manual review, record the procedure, result, owner, and proof limits.
- Every evidence item also states what it does not prove: production cardinality, tenant skew, replay scale, replica lag, downstream consumer compatibility, or rollback under live traffic.
- Prefer existing repository tests, query-plan tooling, migration validators, and metrics dashboards before adding new support code.
- Do not accept screenshots alone unless the verified surface is a dashboard, alert, or UI-backed operational view; pair screenshots with query, command, or report evidence when possible.
