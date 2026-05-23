# Security Checks

## Threat Surface

This benchmark touches cache keys, tenant and permission scoping, Redis outage behavior, and fallback access to the source of truth. A flawed implementation can leak cross-tenant data or overload the database during dependency failure.

## Required Checks

- Verify that cache key construction includes tenant, permission, and variant dimensions when applicable.
- Verify that Redis failure does not expose stale unauthorized data.
- Verify that stampede protection fails closed on lock ownership ambiguity.
- Verify that metrics do not include unbounded user identifiers as labels.

## Rejection Cases

- Reject any solution that uses TTL-only mutable cache with no invalidation.
- Reject any solution that omits tenant or permission data from cache keys.
- Reject any solution that has no metric for miss storm or hot key.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
