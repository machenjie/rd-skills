# Cache Design Checklist

- Identify source of truth and confirm cache is only an acceleration or fallback layer.
- Define cache keys, tenant or permission scope, value shape, and ownership.
- Define TTL, jitter, invalidation triggers, and stale tolerance.
- Define stampede protection for hot keys and refresh paths.
- Define penetration protection for missing or attacker-controlled keys.
- Define fallback when cache read, cache write, refresh, or source lookup fails.
- Define observability for hit rate, miss rate, stale serves, evictions, and source load.
- Test invalidation, permission changes, cache outage, and source overload behavior.
