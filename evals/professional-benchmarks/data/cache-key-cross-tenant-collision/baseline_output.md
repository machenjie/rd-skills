The Redis cache is acceptable as drafted.

We can omit tenant from a multi-tenant cache key because user IDs are unique
enough in practice. We can also cache authorization or entitlement state without
invalidation and skip memory cardinality or hot-key review until production
traffic grows.

Add a simple TTL later if needed.
