Selected stage: implementation-planning.
Selected professional skill: data-middleware-change-builder.
Selected capabilities: cache-design, permission-boundary-modeling, observability.

Hidden risks: cross-tenant cache collision; stale authorization or entitlement state; unbounded cache cardinality or hot key.

Inspected boundaries: entitlement source of truth, admin grant-change write path, tenant and user permission boundary, Redis key namespace, TTL/invalidation path, key cardinality estimate, hot-key metrics, and alert owner.

Evidence required: tenant-scoped cache key schema; TTL and invalidation validation evidence; memory cardinality and hot-key monitoring evidence.

Output obligations covered: source-of-truth and cache lifecycle analysis; validation evidence for key isolation and invalidation; residual stale authorization risk owner.

Validation command: `python3 -m pytest tests/data/test_entitlement_cache.py` (not run in fixture; expected outcome is tenant key isolation, grant-change invalidation, TTL, and hot-key metric assertions).
What evidence proves: the inspected entitlement cache key is tenant-scoped, invalidated after grant changes, and instrumented for cardinality and hot-key risk.
What evidence does not prove: production traffic skew, rare cross-region invalidation delay, or all future entitlement shapes.

Residual risk: production hot-key distribution still needs post-rollout sampling; owner: reliability-observability-gate.
Next gate: reliability-observability-gate before production enablement.
