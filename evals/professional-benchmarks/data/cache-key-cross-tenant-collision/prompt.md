Review this cache design:

The team wants to cache authorization entitlement checks in Redis with key
`entitlement:{userId}`. The product is multi-tenant, users can belong to more
than one tenant, entitlement changes are written by an admin workflow, and the
proposal has no tenant in the key, no invalidation on grant changes, no TTL
jitter, and no estimate for key cardinality or hot-key monitoring.

Decide whether the cache design is acceptable and state the evidence required
before implementation.
