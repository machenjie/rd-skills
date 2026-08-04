# NoSQL Database Checklist

- Justify the store model from named access paths, invariants, shape, distribution, and rejected relational/cache/search alternatives.
- Map reads, writes, deletes, ranges, scans, keys, item/document boundaries, and secondary indexes; expose fan-out and unsupported paths.
- Test peak tenant/time/status/key skew, collection growth, hot-key behavior, split/bucket/repartition choices, and deployed limits.
- Define strong or stale reads, read-your-writes, conflicts, and partial effects from invariants classified by item, document, partition, or cross-boundary scope.
- Define duplicate/reordered/unknown write outcomes, version or condition ownership, retry idempotency, reconciliation, and adjacent consistency handoffs.
- Name denormalized source writers, propagation/delete order, staleness, drift detection, replay, repair, and rebuild.
- Prove stored-shape compatibility across old/new readers and writers, versions/defaults, unknown fields, indexes, backfills, and rollback.
- Derive TTL, tombstone, retention, capacity, quota, and recovery behavior from current policy, replay windows, workload, and deployed configuration.
- Map each changed claim to current queries, configuration, data samples, tests, telemetry, proof limits, and owners.
