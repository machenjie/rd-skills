# Cache Design Benchmarks And Patterns

Use this reference when the cache design needs pattern selection, technology selection, defense mapping, HTTP cache security review, observability planning, or graph/memory/execution reconciliation. Keep the cache as an acceleration or fallback layer; never let the cache become the only durable record.

# Benchmark Anchors

- HTTP caches: RFC 9111 for freshness and cacheability, RFC 7232 for conditional requests, RFC 5861 for stale-while-revalidate and stale-if-error, RFC 8246 for immutable assets, and RFC 9211 for `Cache-Status`.
- Critical state: Google SRE guidance treats cache as performance optimization, not durability or authority.
- Distributed cache scale: Memcache-at-scale, TAO, EVCache, Redis, Memcached, Varnish, CloudFront, Fastly, Cloudflare, and Akamai patterns inform namespace isolation, lease tokens, purge granularity, eviction policy, failover, and edge behavior.
- Security: OWASP web cache deception and cache poisoning patterns apply whenever shared caches, path normalization, cookies, authorization headers, unkeyed headers, or high-cardinality `Vary` are present.
- Load protection: single-flight, lease tokens, probabilistic early recomputation, TTL jitter, Bloom filters, Cuckoo filters, stale-if-error, request coalescing, source rate limits, and warm-up plans are normal professional controls.

# Pattern Selection Matrix

| Pattern | Read path | Write path | Consistency window | Use when |
| --- | --- | --- | --- | --- |
| Cache-aside | App checks cache, loads source on miss, then populates | Write source, then invalidate or version cache | TTL or invalidation lag | Default application pattern with flexible ownership |
| Read-through | Cache library loads source on miss | Write source, then evict or update cache | TTL or invalidation lag | Uniform load behavior is more valuable than simple app code |
| Write-through | Reads use cache | Synchronously write cache and source | Stronger cache freshness | Writes can tolerate latency and failure semantics are explicit |
| Write-behind | Reads use cache | Cache accepts write, source flush is async | Cache can lead source | Rare; only if data-loss risk is explicitly accepted and durable queue semantics exist |
| Refresh-ahead | Reads use cache | Background refresh before expiry | Near-real-time for hot keys | Predictable hot keys and source latency need smoothing |
| Versioned key | Reader resolves current version, then reads immutable value | Write bumps version | Atomic per version pointer | Config, content, feature state, and data where purge complexity is high |
| Materialized view | Read precomputed projection | Source changes trigger refresh | Refresh-window bound | Reused joins or aggregates with known staleness tolerance |
| HTTP / CDN | Shared cache serves and revalidates with origin | Origin sets headers and purge tags | `max-age`, `s-maxage`, or validation | Public or safely partitioned content at high geographic fanout |

# Technology Selection Matrix

| Technology | Fit | Main risk |
| --- | --- | --- |
| Request memoization | One request or unit of work | Accidentally leaking across requests or users |
| In-process LRU | Per-pod hot config, decoded metadata, tiny stable values | Multi-pod inconsistency and memory pressure |
| Memcached | Simple high-throughput ephemeral key/value | No replication or complex data model |
| Redis | Complex data types, pub/sub invalidation, distributed leases | Mistaking cache for transactional source of truth |
| Managed Redis/Memcached | Production cache availability and operations | Cost, cross-AZ latency, and hidden failover assumptions |
| CDN or reverse proxy | Static, public, or carefully keyed edge content | User data leakage, poisoning, purge complexity |
| Database materialized view | Reused aggregate or read model | Refresh cost and stale analytics assumptions |
| Search result cache | Repeated expensive search queries | Low reuse from highly diverse query space |

# Defense Decision Tree

| Condition | Required defense |
| --- | --- |
| Single hot key expires | Single-flight per process plus cluster lease or origin-side rate limit |
| Many keys share expiry | TTL jitter, probabilistic early refresh, and staggered warm-up |
| Cache cluster restarts | Request coalescing, source token bucket, stale-if-error, and warm-up |
| Attacker controls key space | Negative cache with short TTL, rate limit, normalization, and existence filter where practical |
| Bounded legitimate key set exists | Bloom or Cuckoo filter to reject definitely-absent keys before source lookup |
| Authorization-sensitive value | Identity or permission version in key, event invalidation, and TTL at or below propagation SLA |
| Cross-region cache path | Declare replication lag and avoid strong decisions on eventually replicated cache data |

# Key And Value Schema Pattern

Each cache class needs a key template, value schema, owner, and migration rule:

```text
v{schema_version}:tenant:{tenant_id}:perm:{permission_version}:resource:{normalized_resource_key}
```

- Put tenant, user, role, permission-set version, locale, representation, and schema version in the key when they affect the value.
- Exclude request id, trace id, unbounded headers, raw user input, and noisy query parameters unless normalized and intentionally part of the representation.
- Version value schema in the key prefix so rolling deploys never mix old readers with new shapes.
- Hash sensitive identifiers when they must participate in the key; do not log secrets, tokens, or raw PII.
- Estimate key count, value size, and eviction behavior before selecting memory limits.

# Correctness-Sensitive Caches

| Cached value | Required bound |
| --- | --- |
| Permission or PDP decision | Event invalidation on grant change; TTL no longer than propagation SLA |
| Pricing or promotion | Campaign owner accepts stale window; writes purge or bump version |
| Inventory or reservation | Avoid cache for final decision unless source confirms; stale read must not oversell |
| Balance, limit, fee, or ledger-derived state | Cache is display-only unless source rechecks before action |
| Compliance or audit record | Prefer no cache or explicit erasure/invalidation path |
| Feature or policy config | Versioned key or config revision in key; rollout and rollback path named |

# HTTP And CDN Security Review

- Use `private` or `no-store` for personalized or sensitive responses; use `s-maxage` only when shared-cache safety is established.
- Keep `Vary` minimal and representation-driven. Avoid `Vary: User-Agent` unless the response truly changes by user agent.
- Strip or key every input that can affect the response, including forwarded host, forwarded scheme, original URL, locale, auth-derived role, and content negotiation headers.
- Normalize dynamic routes that look like static assets, and prevent extension suffix tricks from causing private responses to be cached as public assets.
- Use surrogate keys or cache tags for targeted purge; avoid global or per-URL purge assumptions when write volume is high.
- Test that `Set-Cookie`, authorization headers, and user-specific content cannot be stored in a public/shared cache.

# Observability And Validation Map

| Signal or test | Purpose |
| --- | --- |
| Hit, miss, stale serve, bypass, and refresh failure count | Shows cache decisions and freshness behavior |
| Source-load delta and hit-rate cliff alert | Detects miss storm before source overload |
| Hot-key top-N and key-cardinality estimate | Reveals skew hidden by aggregate hit rate |
| Eviction count, memory pressure, item size, and fragmentation | Detects capacity risk and tail-latency pressure |
| Cache-down drill or fake-cache fallback test | Proves source can serve under backpressure |
| Concurrent same-key worker test | Proves single-flight or lease behavior |
| Negative-cache transient miss test | Proves short TTL and recovery from false absence |
| Permission revoke or pricing update test | Proves correctness-sensitive invalidation |
| `Cache-Status` or equivalent header/log | Makes HTTP/edge decisions auditable |

# Graph, Memory, And Execution Coupling

- Treat repository graph, skill memory, issue history, and previous reports as hypotheses about cache behavior, not evidence by themselves.
- Before completion, reconcile those hypotheses with current touched files, registry entries, tests, config, generated reports, command output, and the route selected for the current change.
- Mark evidence stale when key schema, TTL, invalidation, permissions, serialization, cache topology, edge rules, deployment path, or validation scripts changed after the last report.
- Record whether inspected commands were read-only or state-mutating; cache flushes, purges, cloud commands, build/install operations, and production telemetry access require explicit permission and sandbox notes.
- Keep validation claims bounded: local fake-cache tests do not prove production cardinality, regional propagation, memory pressure, rare races, or real traffic skew unless those were measured.

# Anti-Patterns To Reject

| Anti-pattern | Failure |
| --- | --- |
| Tenant or permission omitted from the key | Cross-tenant or cross-user leakage when keys collide |
| Permission applied only after cached object fetch | Shared object can expose unauthorized fields |
| Identical TTLs across a large key class | Coordinated expiry and stampede |
| Negative cache with no TTL | Transient absence becomes permanent absence |
| Cache restart without warm-up or source backpressure | Origin overload on first traffic wave |
| Public cache on response with cookie-derived user data | Shared cache can serve one user response to another |
| Unkeyed request header affects response | Poisoned shared response served to later users |
| Write-behind without durable failure contract | Cache loss becomes data loss |
| Raw unnormalized user input in key | Poisoning, unbounded cardinality, and poor hit rate |
| Healthy aggregate hit rate without hot-key view | Concentrated misses remain invisible |
