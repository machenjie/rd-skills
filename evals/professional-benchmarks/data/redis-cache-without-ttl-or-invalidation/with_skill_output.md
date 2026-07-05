Selected stage: implementation-planning.
Selected professional skill: data-middleware-change-builder.
Selected capabilities: cache-design, performance-budgeting, observability, permission-boundary-modeling.

Hidden risks: stale entitlement state; cross-tenant cache collision; unbounded Redis memory growth or hot key.

Inspected boundaries: entitlement source of truth, tenant/account permission boundary, Redis key namespace, write paths that change grants, stale-read tolerance, memory and hot-key metrics.

Evidence required: cache key schema with tenant boundary; TTL and invalidation strategy; cache hit, memory, and stale-read validation evidence.

Validation command: `python3 -m pytest tests/data/test_entitlement_cache.py` (not run in fixture; expected outcome is stale-read and invalidation test output).
What evidence proves: tenant-scoped keying, invalidation after entitlement change, bounded stale-read behavior, and cache metrics emission.
What evidence does not prove: production hot-key distribution under launch traffic.

Output obligations covered: source-of-truth and cache lifecycle analysis; validation evidence for invalidation behavior; residual staleness risk and owner.

Residual risk: hot-key estimate requires production traffic sampling after rollout; owner: reliability-observability-gate.
Next gate: reliability-observability-gate for memory and hit-rate alert thresholds.
