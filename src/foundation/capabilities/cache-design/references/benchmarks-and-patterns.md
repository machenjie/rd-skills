# Cache Pattern Selection And Evidence

**Load when:** cache correctness depends on selecting a read/write pattern, key scope, freshness/invalidation, load protection, fallback, or shared-edge behavior.

**Do not load when:** the root Skill already determines the bounded cache behavior or no cache topology/source-load decision changes.

Select thresholds and mechanisms from the current source of truth, process/pod/region topology, key distribution, expiry shape, write rate, origin capacity, stale tolerance, data classification, platform capability, and measured traffic. Cache-aside and every defensive mechanism are candidates, not defaults.

## Decision Questions

1. **Pattern and ownership:** which cache pattern best matches current ownership and failure semantics?
   - Reject write-behind unless durability and repair are explicit.
2. **Key and value scope:** which tenant, user, permission or policy revision, locale, representation, schema version, and normalized input affect the value? Derive an enforced key, namespace, or partition boundary from those dimensions. Evidence should show shared or edge caches remaining within authorization and personalization scope.
3. **Freshness and invalidation:** derive stale bounds and an invalidation mechanism from the least-tolerant consumer, write or propagation behavior, correctness evidence, and platform support.
4. **Stampede and expiry:** When hot keys, synchronized expiry, restart/failover, or cross-pod concurrency can overload the origin, choose a topology-appropriate outcome. Options include coalescing, a lease, early refresh, stagger/jitter, stale fallback, warm-up, or origin limiting. Do not add them without that risk.
5. **Penetration and key-space abuse:** When attacker-controlled or high-cardinality misses threaten the origin, choose normalization, admission/rate control, bounded negative caching, or an existence filter. The legitimate key set, false-result behavior, and recovery needs determine the choice.
6. **Failure and capacity:** document how selected behavior protects correctness and the source for each triggered failure path. Disclose untested triggered paths and keep telemetry scoped to owned decisions.

## Evidence Outcomes

- Current key/value schema and cache/source write paths identify ownership, invalidation order, serialization/version coexistence, and sensitive-data handling.
- Traffic/config evidence bounds hit/miss/stale rates, expiry concentration, hot-key skew, memory/item pressure, and source-load delta without treating aggregate hit rate as sufficient.
- Tests cover only triggered risks: scope collision, concurrent same-key load, transient absence, permission/price/inventory update, cache outage, restart/failover, edge poisoning, or source overload.
- State regional propagation, production cardinality, failover, rare-race, and traffic-skew proof limits for local fake-cache tests.

## Failure Patterns

- Cache-aside chosen by habit even though uniform loading, write ordering, or platform ownership requires another pattern.
- In-process coalescing presented as cross-pod protection, or TTL jitter added despite no coordinated-expiry risk.
- Negative cache/filter used without false-absence recovery, bounded lifetime, or evidence of penetration risk.
- Personalized responses or permission-sensitive values share a key/cache boundary that omits identity or policy revision.
- Cache restart or broad invalidation can drive origin load beyond measured safe capacity.
