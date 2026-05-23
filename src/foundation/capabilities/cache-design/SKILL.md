---
name: cache-design
description: Designs cache behavior with explicit source of truth, TTL, invalidation, stampede protection, penetration protection, consistency tolerance, and fallback.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "49"
changeforge_version: 0.1.0
---

# Mission

Design caches as **bounded acceleration layers**, never as the source of truth — with explicit ownership, freshness tolerance, key scoping, invalidation strategy, stampede protection, penetration protection, fallback behavior, consistency model, and observability — so that hit rate is achieved without leaking data across tenants, serving stale-but-dangerous values, amplifying outages, or burying correctness defects behind a 99% hit rate.

# When To Use

Use this capability when a change adds or modifies: in-process memoization (LRU caches, request-scoped memoization), distributed caches (Redis, Memcached, ElastiCache, Cloud Memorystore), HTTP caches (`Cache-Control`, ETag, conditional requests, RFC 9111), edge / CDN caches (CloudFront, Fastly, Cloudflare, Akamai), GraphQL persisted-query / response caches, ORM second-level caches (Hibernate L2), database query result caches, materialized views used as caches, RPC client-side caches, JWT/JWKS/policy decision caches, negative caches, fragment caches, search-index caches, or any cache-backed fallback / degradation behavior.

# Do Not Use When

Do not use this capability to **make cache the source of truth**, to mask a slow query that should be fixed (`indexing-query-optimization`), to mask a wrong data model (`data-model-design`), to mask permissions enforcement defects (`authentication-authorization`), or to substitute for a specialized read engine (`search-analytics-design`). Cache is acceleration; it cannot rescue incorrect logic, missing indexes, or weak isolation.

# Non-Negotiable Rules

- **Cache is not source of truth.** Cache loss must never lose data and must never change behavior beyond stated stale tolerance.
- **Per cached value declare**: owner, source of truth, key schema (with version), value shape (with version), TTL (with jitter), invalidation triggers, consistency tolerance, scope (tenant/user/permission), serialization format, max size + eviction policy.
- **Tenant + permission scoping in the key**, not in post-fetch filtering. Permission filter applied after cache lookup → cross-tenant leak when keys collide. Pattern: `v{schemaVer}:t{tenant}:u{user|role}:{logical-key}`.
- **TTL is jittered.** Identical TTLs on a class of keys → coordinated expiry → synchronized stampede. Apply ±10–30% jitter.
- **Stampede protection** is mandatory for hot keys: single-flight / request coalescing (one upstream call per key per process+cluster), distributed lock with short timeout + fallback to stale, or probabilistic early refresh (XFetch).
- **Penetration protection** for missing keys: negative cache with bounded TTL **and** bloom filter / explicit existence index. Never let unbounded miss-flood reach the source.
- **Avalanche protection** for cache restart / cluster failover: warm-up plan, request coalescing, source-rate limiting (circuit breaker / token bucket on origin), staged TTL on cold start.
- **Stale-while-revalidate / stale-if-error** are first-class behaviors, declared and bounded, not accidental.
- **Invalidation is bound to write paths** (publish on commit, outbox events, CDC), or replaced by versioned keys (read-the-version-then-the-value). "We'll periodically clear the cache" is not invalidation.
- **Authorization decisions, entitlement, pricing, inventory, balance** carry tight TTL or explicit invalidation; no implicit "a few minutes won't matter".
- **Cache failure mode is graceful degradation**: source still serves; do not fail closed because Redis is down. Apply backpressure to protect source.
- **Observability** mandatory: hit rate, miss rate, stale-serve count, eviction count, refresh failure count, key-cardinality, hot-key concentration, source-load impact, cache memory pressure. Alert on hit-rate cliff and miss storm.
- **Serialization format and value schema are versioned** in the key prefix; rolling deploys with mixed versions must not mix shapes (otherwise readers crash on unexpected fields).
- **No secrets, tokens, or PII in cache logs/keys**; key may contain hashed identifiers.

# Industry Benchmarks

Anchor against: **RFC 9111 (HTTP Caching)** for response cacheability, freshness, validation, and `Cache-Control` directives (`no-store`, `no-cache`, `private`, `public`, `s-maxage`, `stale-while-revalidate` per **RFC 5861**, `immutable` per **RFC 8246**); **RFC 7232 (Conditional Requests)** for ETag/`If-None-Match` validation; **RFC 9211 (`Cache-Status`)** for cache observability headers. **Google SRE Workbook — Managing Critical State** (cache as performance optimization, never as durability). **Facebook Memcache @ Scale (NSDI '13)** lessons: lease tokens for stampede control; gutter pool for failover; key namespace isolation. **Facebook TAO** for read-optimized graph cache with consistency contract. **Netflix EVCache** patterns. **Twitter "Pelikan" / Memcached at scale** lessons. **Redis best practices** — appropriate eviction policy (`allkeys-lru`, `allkeys-lfu`, `volatile-ttl`), persistence trade-offs (RDB/AOF), keyspace notifications, cluster slot mapping, **Redis 6+ ACL** for tenant isolation, **client-side caching with invalidation (RESP3 tracking)**. **Memcached** consistent hashing (Ketama) for minimal redistribution on node change. **CDN caching**: **AWS CloudFront**, **Fastly VCL**, **Cloudflare cache rules**, **Akamai**; cache-key normalization, query-string allowlist, vary-on header discipline, surrogate keys / cache tags for targeted purge. **Varnish** patterns: TTL + grace + keep. **OWASP Web Cache Deception** (CVE class — attacker tricks shared cache into storing a private response under a public key). **OWASP Cache Poisoning** (unkeyed input poisons shared cache). **GoF / groupcache (Brad Fitzpatrick)** single-flight pattern. **Probabilistic Early Recomputation (XFetch)** — Vattani et al., 2015. **Bloom filter** (Burton Bloom 1970) for negative-existence acceleration; **Cuckoo filter** for deletable membership.

### Cache Pattern Selection Matrix

| Pattern | Read path | Write path | Consistency window | Pick when |
| --- | --- | --- | --- | --- |
| **Cache-aside (lazy)** | App reads cache → miss → load source → populate | App writes source, **invalidates** cache | TTL or invalidation lag | Default for most apps; flexible; risk of stampede on cold key |
| **Read-through** | App reads cache; cache loads source on miss | App writes source; cache evicts/updates | TTL or invalidation lag | Encapsulated cache library; uniform load behavior |
| **Write-through** | App reads cache | App writes cache **and** source synchronously | Strong (cache always fresh) | Read-heavy + tolerable write latency |
| **Write-behind (write-back)** | App reads cache | App writes cache; async flush to source | Cache leads source by flush window | Very write-heavy; **dangerous** — cache loss = data loss; rarely acceptable |
| **Refresh-ahead** | App reads cache | Background refresh before TTL expires | Near-real-time | Predictable hot keys; absorbs source latency |
| **Versioned-key (immutable)** | Read `v:{ver}:{key}` after reading current `ver` | Bump `ver` on write | Atomic per key | Avoids invalidation complexity; great for content / config |
| **Materialized view as cache** | Read pre-aggregated view | Source writes trigger view refresh | View refresh window | Expensive aggregations; analytics; bounded staleness ok |
| **HTTP / CDN cache** | Edge serves; revalidate with ETag | Origin sets `Cache-Control`; purge via tag | Per `max-age`/`s-maxage` | Public assets; geographic distribution; high egress savings |

### Cache Technology Selection

| Technology | Topology | Best for | Avoid when |
| --- | --- | --- | --- |
| **In-process LRU (Caffeine, lru-cache)** | Per pod | Per-pod hot config, decoded JWT, tiny hot keys | Multi-pod consistency required; large dataset |
| **Memcached** | Sharded, no replication | Simple key/value, ephemeral, high throughput | Need replication, persistence, complex types |
| **Redis (single / sentinel / cluster)** | Replicated, optional persistence | Complex types (sets, sorted sets, streams), pub/sub invalidation, distributed locks | Need transactional source-of-truth (it isn't one) |
| **Cloud-managed (ElastiCache / MemoryDB / Memorystore)** | Managed Redis/Memcached + multi-AZ | Production durability/availability of Redis | Cost-sensitive dev/test |
| **CDN (CloudFront/Fastly/Cloudflare)** | Edge POPs | Static + cacheable responses; geographic reach | Per-user dynamic content (or use surrogate keys + Vary carefully) |
| **Materialized view in DB** | Same DB | Aggregate/joins reused widely | High write rate making refresh expensive |
| **Search engine result cache (Elastic / OpenSearch)** | Same engine | Repeated queries on slow indices | Tiny diverse query space |

### Stampede / Penetration / Avalanche — Defense Decision Tree

```
Hot key with sudden expiry?
├─ Single hot key → single-flight (groupcache) per process; distributed lease (Memcache lease tokens) cluster-wide.
├─ Many keys expiring together → TTL jitter (±20–30%) + probabilistic early refresh (XFetch).
├─ Cache cluster restart / failover → request coalescing + origin-side rate limit + stale-if-error fallback + warm-up plan.
Missing key flood (penetration)?
├─ Bounded set of legitimate keys → bloom filter / cuckoo filter at edge.
├─ Open key space → negative cache with short TTL + per-IP rate limit; never unbounded passthrough.
Authorization-sensitive value?
├─ Always include identity + permission version in key; invalidate on permission change; bound TTL ≤ permission propagation SLA.
```

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| Cache key omits tenant; permission applied after fetch | Cross-tenant data leak when keys collide |
| All product-detail keys TTL=600s set at deploy | Synchronous expiry → coordinated stampede every 10 min |
| Negative cache stores `null` with no TTL | Once a key is missing, it stays "missing" forever |
| Cache restart without warm-up | Origin meltdown on first traffic wave |
| Pricing cached 1 hour for "performance"; promo launches | Customers see old prices, support storm, revenue dispute |
| Authorization decision cached 5 min after revoke | Revoked admin still acts for 5 minutes |
| `Cache-Control: public` on response containing `Set-Cookie` user data | CDN serves user A's response to user B (web cache deception) |
| Vary on `User-Agent` (high cardinality) | Cache hit rate collapses |
| Write-behind to keep latency low; Redis crashes | Last 30 s of writes lost; data integrity broken |
| Key includes raw user input not normalized | Cache poisoning / unbounded cardinality |

# Selection Rules

Select this capability when **cache behavior is primary**. Adjacent routing:

- Prefer `indexing-query-optimization` when the source query itself is the actual bottleneck — fix the query before adding cache.
- Prefer `search-analytics-design` when the workload requires a specialized read engine.
- Prefer `data-model-design` when read shape mismatches storage shape — denormalize or project rather than over-cache.
- Prefer `reliability-observability-gate` for broader degradation, fallback, and overload planning.
- Prefer `authentication-authorization` for permission-decision caching policy (PDP cache TTL, invalidation on grant change).
- Prefer `web-security` for CSRF / cookie / cache-deception interactions on shared HTTP caches.
- Use **with** `observability` for cache-specific signals.

# Risk Escalation Rules

Escalate when cached data affects: permissions / authorization decisions, pricing / discounts / promotions, financial state (balances, limits, fees), inventory / reservations, compliance records, audit data, tenant isolation in multi-tenant systems, high-traffic hot keys (single key > a few % of total load), launch events / flash sales (predictable stampede), shared HTTP caches (CDN/edge) on responses containing per-user data, scenarios where a cache-miss storm could exceed source capacity, or where cache loss could cause data loss (write-behind). Escalate any new cross-region or shared-edge cache configuration.

# Critical Details

Cache correctness is defined by **what staleness is acceptable, for how long, under what failure mode, and to whom**. Apply these refinements:

- **Cache key design.** Include: schema version, tenant, identity (or permission-set version where applicable), normalized inputs, content negotiation. Exclude: noise (request id, traceparent, unbounded headers). Normalize input (lowercase, sort, canonicalize) to maximize hit rate without poisoning.
- **Value schema versioning.** Bump `v{N}` in key prefix when shape changes; do not mutate in place. Old pods reading new shape (or vice versa) crash or corrupt during rolling deploy.
- **TTL choice.** Driven by (a) maximum acceptable staleness for the *least-tolerant consumer*, (b) source recompute cost, (c) write rate and invalidation reliability. Add jitter; document the choice.
- **Invalidation reliability.** "Publish + best-effort delete" loses messages; prefer outbox + CDC, or versioned keys, for correctness-critical invalidation.
- **Single-flight is per scope.** In-process single-flight does not protect across pods. Cluster-wide protection needs distributed lease / lock or origin-side rate limit.
- **Probabilistic early recomputation (XFetch)** refreshes a fraction of requests *before* TTL with probability rising near expiry → eliminates synchronized expiry without coordinator.
- **Hot-key detection.** Sample top-N by request rate; large gap between #1 and #10 means split or replicate the hot key (e.g., shard `key#0..N`, client picks shard).
- **Permission cache TTL** must be ≤ permission propagation SLA. Cached PDP decisions need invalidation on grant change (event-driven), not just TTL.
- **HTTP cache correctness.** `Cache-Control: private` for per-user; `s-maxage` for shared; `Vary` on the *minimum* set of headers that affect representation; never `Vary: User-Agent` unless content actually depends on UA. `no-store` for sensitive responses.
- **Cache deception.** Attacker requests `/profile/foo.css` — origin serves `/profile`, edge caches under `.css` (treated as static) → next user gets victim's profile. Defense: normalize path, deny dot-extension on dynamic routes, set `Cache-Control: private` defensively.
- **Cache poisoning via unkeyed input.** Headers like `X-Forwarded-Host`, `X-Forwarded-Scheme`, `X-Original-URL` may influence response but not be in the cache key → attacker poisons. Defense: include in key or strip at edge.
- **CDN purge granularity.** Per-URL purge is slow + costly at scale. Use **surrogate keys / cache tags** (Fastly, Cloudflare) so a write event purges only affected tags.
- **Negative cache with bloom filter.** Bloom filter at edge answers "definitely not present" → short-circuit without origin call. Cache `null` answers with short TTL for items confirmed absent.
- **Eviction policy.** `allkeys-lru` for general; `allkeys-lfu` for skewed access; `volatile-ttl` only when most keys have TTL and you want the soonest-to-expire evicted first. Wrong policy → working set evicted under memory pressure, hit rate collapses.
- **Memory pressure → tail latency.** Redis approaching `maxmemory` evicts on every write → p99 latency spikes. Alert on memory % well before maxmemory.
- **Connection pooling and pipelining.** Redis is fast; the network round trip dominates. Use pipelining for batch reads; tune pool size to avoid connection storms on cold start.
- **Cache loss drill.** Periodically (in non-prod) flush cache and confirm: source survives, no error spike, hit rate recovers within target. Untested = unknown.
- **Multi-region.** Cross-region replication has lag; do not use distributed cache for strongly-consistent decisions across regions.
- **Observability headers.** Emit `Cache-Status` (RFC 9211) so it is visible *what* the cache decided and why (hit/miss/bypass/stale).
- **GDPR / data subject erasure.** Cached PII must be invalidated on erasure; document the path. Long-TTL cached PII is a compliance risk.

# Failure Modes

- Stale cache shows revoked permissions, old pricing, deleted records, or cancelled orders.
- Popular key expires; thousands of requests stampede the database simultaneously → cascading outage.
- Missing-key flood lets attackers force repeated expensive lookups; no negative cache or bloom filter in place.
- Cache keys omit tenant or permission scope → cross-tenant or cross-user data leak when keys collide.
- Synchronized TTL expiry (no jitter) coordinates a wave of misses every N seconds.
- Cache cluster restart / failover triggers cold-cache origin meltdown.
- Web cache deception serves user A's private response to user B from a shared CDN.
- Cache poisoning via unkeyed header rewrites poisons the response served to all subsequent users.
- Write-behind cache loses last-N writes when Redis crashes → data loss masquerading as cache loss.
- Hit rate looks healthy (e.g., 95%) but a single hot key drives 80% of misses → invisible source pressure.
- Cache value schema rolled out without key versioning; old pods crash on new shape during rolling deploy.
- Negative cache without TTL turns transient miss into permanent "not found".
- Permission-decision cache TTL longer than admin's expectation → revoked admin still acts.
- Eviction policy mismatch (e.g., `noeviction`) → writes start failing under memory pressure.
- CDN per-URL purge cannot keep up with write rate → stale spreading globally.
- `Vary: User-Agent` collapses hit rate; switching to `Vary: Accept-Encoding` recovers it.
- PII cached with long TTL violates erasure SLA.

# Output Contract

Return a cache strategy with, per cached value class:

- `purpose` (latency reduction, source protection, fallback, edge distribution)
- `source_of_truth` (system, table/endpoint)
- `owner` (team/role)
- `key_schema` (template with version: `v{N}:t{tenant}:u{identity}:{logical}`; normalization rules; cardinality estimate)
- `value_shape` (schema, version, serialization format, max size)
- `tier` (in-process / distributed / HTTP / CDN / materialized view) and **technology choice rationale**
- `pattern` (cache-aside / read-through / write-through / write-behind / refresh-ahead / versioned-key)
- `ttl` (base + jitter %; per-class)
- `consistency_tolerance` (max acceptable staleness; consumer-named)
- `invalidation` (write-path triggers, outbox/CDC, version bump, surrogate-key purge)
- `stampede_protection` (single-flight scope, lease, XFetch, lock-with-fallback)
- `penetration_protection` (negative cache TTL, bloom/cuckoo filter, rate limit)
- `avalanche_protection` (warm-up, request coalescing, source rate limit, stale-if-error)
- `tenant_permission_scoping` (key composition; PDP cache invalidation on grant change)
- `failure_mode` (cache down → degrade-and-serve from source under backpressure; bounds documented)
- `eviction_policy` and **memory headroom alert threshold**
- `observability` (hit/miss/stale/eviction/refresh-failure/source-load/hot-key/memory metrics; alerts; `Cache-Status` header where HTTP)
- `security` (no secrets in keys/logs; hashed PII; HTTP cacheability + Vary review; deception/poisoning defenses)
- `gdpr_erasure_path` (where applicable)
- `tests` (correctness under: stale, miss flood, stampede, cache-down, schema-version mixed deploy, permission revoke, invalidation race)
- `rollout_plan` (warm-up, canary, kill-switch, rollback)

# Quality Gate

The strategy passes only when:

1. **Source of truth is named** and cache is explicitly *not* it.
2. **Per cached class**: purpose, key schema (with version + tenant + identity scope), value schema, TTL with jitter, invalidation, consistency tolerance are documented.
3. **Stampede, penetration, and avalanche protection** are designed (not assumed) for hot keys and cold-start.
4. **Tenant + permission scope** is in the key, not in post-fetch filtering.
5. **Cache failure degrades gracefully** (source still serves under backpressure); cache-loss drill executed or scheduled.
6. **Authorization / pricing / financial / inventory caches** have invalidation tied to the underlying event, not pure TTL guess.
7. **Schema versioning** allows safe rolling deploys without mixed-shape crashes.
8. **Observability**: hit/miss/stale/eviction/source-load/memory metrics emitted; alerts on hit-rate cliff, miss storm, hot-key concentration, memory pressure.
9. **HTTP/CDN caches** reviewed for correctness of `Cache-Control`, `Vary`, surrogate keys; deception and poisoning vectors closed.
10. **No secrets, tokens, or unredacted PII** in keys or logs; PII has erasure path.
11. **Tests** cover stale, miss flood, stampede, cache-down, mixed-version deploy, permission revoke, invalidation race.
12. **Rollout plan** includes warm-up, canary, kill-switch, and a documented rollback that does not depend on cache being healthy.

# Used By

- data-middleware-change-builder
- reliability-observability-gate

# Handoff

Hand off to `indexing-query-optimization` when the underlying source query needs to be fixed; `data-model-design` when the read shape requires denormalization; `search-analytics-design` when a specialized read engine is the right answer; `authentication-authorization` for permission-decision cache invalidation; `web-security` for HTTP cache deception / poisoning review; `reliability-observability-gate` for degradation policies and overload protection; `observability` for cache-specific signal design; `backend-change-builder` for implementation.

# Completion Criteria

The capability is complete when **the cache demonstrably accelerates reads within an explicitly bounded staleness budget, never holds the only copy of data, isolates tenants and permissions in the key, defends against stampede / penetration / avalanche, degrades gracefully when the cache itself fails, invalidates correctness-critical values on the write event rather than by TTL guess, exposes hit/miss/stale/source-load signals with alerts, and survives a documented cache-loss drill** — without becoming an uncontrolled source of truth or an outage amplifier.
