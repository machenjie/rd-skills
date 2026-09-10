# Data Middleware Checklist

- Name source of truth and derived stores.
- Define consistency expectations and freshness windows.
- Map read and write access patterns.
- Check indexes, query plans, cardinality, and hot paths.
- Define cache keys, TTL, invalidation, stampede prevention, and stale reads.
- Define queue ordering, delivery semantics, retries, selected terminal handling, and replay.
- Define search indexing, reindexing, and reconciliation.
- Define storage lifecycle, permissions, and recovery.
- Check migration forward path, accepted recovery or containment and irreversible limits, online/offline execution, batching, lock risk, and resumability.
- Confirm dependency lifecycle for clients, pools, streams, subscriptions, and shutdown cleanup.
- Reuse current signals and checks that prove the changed mechanism; add metrics, alerts, release-watch signals, or regression tests only for actual gaps or required operating decisions.
- Record validation command, validator, output/report artifact, exit code, evidence limit, residual risk, and owner.

## Professional Decision Rules

- Name the source of truth, consistency model, transaction boundary, and ownership for every stateful change.
- Design the required version coexistence, backfill idempotency, restartability, verification, and accepted recovery or owned irreversible boundary.
- For caches and queues, define invalidation, ordering, duplication, replay, poison-message, and degradation behavior.
- Use realistic data volume and concurrency evidence for query, index, lock, and partition choices.

## High-Value Gotchas

- Cache invalidation without a source-of-truth rule serves stale data.
- A migration that cannot resume safely turns failure into manual recovery.
- Queue acknowledgement order can lose or duplicate work.

## Execution Checklist

1. **Analysis mode:** select consistency and recovery behavior from sink evidence.
2. **Task mode:** apply the accepted boundary with replay and reconciliation behavior.
3. Stop when state ownership or reconciliation remains implicit.
