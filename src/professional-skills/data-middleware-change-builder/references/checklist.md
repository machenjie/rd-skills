# Data Middleware Checklist

- Name source of truth and derived stores.
- Define consistency expectations and freshness windows.
- Map read and write access patterns.
- Check indexes, query plans, cardinality, and hot paths.
- Define cache keys, TTL, invalidation, stampede prevention, and stale reads.
- Define queue ordering, delivery semantics, retries, dead letter handling, and replay.
- Define search indexing, reindexing, and reconciliation.
- Define storage lifecycle, permissions, and recovery.
- Check migration forward path, rollback path, online/offline execution, batching, lock risk, and resumability.
- Confirm dependency lifecycle for clients, pools, streams, subscriptions, and shutdown cleanup.
- Add metrics, alerts, release-watch signals, and regression tests.
- Record validation command, validator, output/report artifact, exit code, evidence limit, residual risk, and owner.
