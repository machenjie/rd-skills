# Cache Design Proof Checklist

- Prove the source of truth, cache owner, loss behavior, and accepted stale/fallback outcome.
- Prove key/value scope covers only dimensions that change representation, including tenant or permission context when applicable.
- Prove the selected read/write pattern fits actual ownership, atomicity, platform, and failure behavior; cache-aside is one candidate, not the default.
- When hot-key, synchronized-expiry, restart, or multi-pod load threatens the origin, select and test a topology-appropriate coalescing, lease, refresh, staggering/jitter, stale, warm-up, or rate-control outcome.
- When attacker-controlled or unbounded misses threaten the origin, select a tested normalization, admission or rate control, bounded negative-cache, or existence-filter control with false-absence recovery.
- Prove freshness and invalidation against the least-tolerant consumer and actual commit/write path; TTL, purge, versioning, revalidation, or event invalidation are candidates.
- For reachable failures under the selected cache pattern or topology, test applicable read, write, refresh, eviction, cold-start, stale-serving, source-overload, and regional paths. Record untested triggers and the limits of non-production load evidence.
- Select hit/miss/stale/eviction/hot-key/cardinality/source-load signals only when they answer an owned operational decision.
