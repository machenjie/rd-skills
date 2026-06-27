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

# Stage Fit

Use during planning, coding, bug-fix, debugging, code-review, refactoring, testing, release, and handoff when cache behavior, cache evidence, or a remembered cache claim can change source load, freshness, tenant isolation, or fallback behavior.

- **Discovery / planning:** use when a proposal introduces a cache tier, edge cache rule, request memoization, materialized read projection, or stale fallback and the source of truth, staleness budget, and invalidation owner are not yet explicit.
- **Implementation / review:** use when cache keys, value schemas, TTLs, invalidation events, negative caches, hot-key controls, or HTTP cache headers are being added or changed.
- **Testing / verification:** use when evidence must prove key isolation, invalidation, stale-window bounds, stampede protection, cache-down fallback, and observability without depending on live cache infrastructure.
- **Release / incident repair:** use when a cold cache, cache cluster restart, edge purge, hit-rate cliff, miss storm, stale authorization/pricing/inventory value, or cache poisoning/deception incident can overload source systems or leak data.
- **Graph / memory / execution coupling:** use project graph and memory as leads only; revalidate against current cache code, config, tests, registry, telemetry, and command output before claiming a cache path is safe.

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
- **Stampede controls need executable local proof**: tests should use deterministic fake/in-memory cache and a clearly named FakeBackend or source-of-truth seam to drive concurrent same-key workers, prove only one refresh happens with an assertion such as `backend.calls == 1`, prove Redis-down fallback/backpressure behavior, and avoid live Redis, network clients, URL literals, or new package dependencies unless the task explicitly requires them.
- **Serialization format and value schema are versioned** in the key prefix; rolling deploys with mixed versions must not mix shapes (otherwise readers crash on unexpected fields).
- **No secrets, tokens, or PII in cache logs/keys**; key may contain hashed identifiers.

# Industry Benchmarks

Anchor against RFC 9111 / 7232 / 5861 / 8246 / 9211 for HTTP freshness, validation, stale extensions, immutable assets, and cache observability; Google SRE guidance that cache is performance optimization rather than critical state; Memcache-at-scale / TAO lessons on leases, namespaces, and read-optimized graph caches; Redis / Memcached / CDN / Varnish operational patterns; OWASP web cache deception and cache poisoning; single-flight, probabilistic early recomputation, Bloom filters, and Cuckoo filters. Keep the body lightweight; use [references/checklist.md](references/checklist.md) for implementation checks and [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for pattern, technology, defense, observability, graph/memory, and anti-pattern matrices.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| Request-local cache | Memoization, LRU, request scope | lifetime and identity boundary | unit test or trace | `unit-testing`, `testability-seam-design` | skip when no shared state or stale consequence |
| Distributed cache | Redis, Memcached, ORM L2, hot key | source truth, keys, TTL, invalidation | fake-cache concurrent test and fallback proof | `reliability-observability-gate`, `observability` | skip when source query must be fixed first |
| HTTP / CDN cache | `Cache-Control`, `Vary`, edge rules | public/private boundary and purge | header review and deception/poisoning test | `web-security`, `security-privacy-gate` | skip for purely private non-cacheable responses |
| Negative cache | miss flood, open key space | bounded miss caching and existence filter | transient-miss recovery and flood proof | `input-validation`, `degradation-circuit-breaking` | skip when miss space is bounded and cheap |
| Correctness-sensitive cache | auth, pricing, inventory, finance | event invalidation and stale SLA | revoke/update test and owner acceptance | `authentication-authorization`, `transaction-consistency` | skip if source rechecks before action |
| Degradation cache | stale-if-error, cache outage | source backpressure and kill switch | cache-down drill or scripted fallback test | `reliability-observability-gate`, `release-rollback` | skip when cache failure cannot affect users |
| Evidence freshness | old graph, memory, report, telemetry | current path and validation reconciliation | command exit status and explicit unknowns | `validation-broker`, `agent-tool-permission-sandbox` | skip only for pure wording with no claim change |
| Handoff closure | final answer, PR review, release note, or incident closeout claims cache safety | map final cache claims to fresh validator/test/report evidence and residual unknowns | changed cache-to-validation map, exit codes, artifact/report paths | `plan-execution-consistency`, `quality-test-gate` | skip only when no cache claim is made |

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

# Proactive Professional Triggers

- **Signal:** A cache key omits tenant, identity, permission version, schema version, or normalization. **Hidden risk:** isolation leak, cache poisoning, or mixed-version rollout defect hides behind high hit rate. **Required professional action:** redesign key/value contract and reject post-fetch permission filtering. **Route to:** `cache-design`, `security-privacy-gate`. **Evidence required:** key template, collision boundary, permission test, and redaction rule.
- **Signal:** Authorization, entitlement, pricing, inventory, financial, or compliance data is cached with only a TTL. **Hidden risk:** stale values authorize revoked users, show wrong prices, oversell inventory, or violate an erasure/audit obligation. **Required professional action:** bind invalidation to the source event or version key and get owner-approved stale bounds. **Route to:** `authentication-authorization`, `transaction-consistency`. **Evidence required:** revoke/update test, invalidation path, SLA, and residual stale window.
- **Signal:** Hot key, launch event, cold start, restart, or cache outage can move traffic to the source. **Hidden risk:** miss storm or coordinated expiry cascades into source overload. **Required professional action:** add single-flight, lease, jitter, stale-if-error, warm-up, and origin backpressure. **Route to:** `reliability-observability-gate`, `degradation-circuit-breaking`. **Evidence required:** concurrent same-key proof, cache-down drill, hit-rate alert, and source-load guardrail.
- **Signal:** Missing keys are attacker-controlled, unbounded, or expensive to prove absent. **Hidden risk:** penetration attack turns misses into repeated source lookups. **Required professional action:** add short negative TTL, existence filter or allowlist, normalization, and rate limits. **Route to:** `input-validation`, `degradation-circuit-breaking`. **Evidence required:** transient-miss recovery test, flood test, TTL bound, and false-positive handling.
- **Signal:** HTTP or CDN cache rules touch cookies, auth headers, personalized responses, extension-routed paths, unkeyed headers, or high-cardinality `Vary`. **Hidden risk:** shared cache deception or poisoning serves one user's response to another. **Required professional action:** review cacheability, `Vary`, path normalization, surrogate keys, and purge path. **Route to:** `web-security`, `security-privacy-gate`. **Evidence required:** header sample, deception/poisoning test, purge proof, and no-store/private decision.
- **Signal:** Project memory, repository graph, old reports, or previous validation says the cache is safe after key, TTL, invalidation, permissions, serialization, topology, or release path changed. **Hidden risk:** stale evidence is reused for a different execution graph. **Required professional action:** reconcile current paths, rerun focused validation, and disclose what remains unknown. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `validation-broker`, `agent-tool-permission-sandbox`. **Evidence required:** inspected path list, accepted/rejected prior claim, command result, sandbox record, and residual risk.

# Critical Details

Cache correctness is defined by **what staleness is acceptable, for how long, under what failure mode, and to whom**. Apply these refinements:

- **Key and value design.** Include schema version, tenant, identity or permission-set version, normalized inputs, content negotiation, serialization, max size, and value version; exclude request ids, trace ids, unbounded headers, and raw sensitive identifiers.
- **TTL and invalidation.** TTL follows least-tolerant consumer stale budget, recompute cost, write rate, and invalidation reliability; jitter every shared TTL and prefer outbox, CDC, or versioned keys for correctness-critical updates.
- **Stampede scope.** In-process single-flight does not protect across pods; cluster-wide protection needs lease/lock, origin rate limit, stale fallback, or probabilistic early recomputation.
- **Hot-key and cold-start control.** Sample top-N key rate, shard or replicate extreme hot keys, warm caches gradually, and prove source survives restart/failover.
- **Test seam.** Expose cache client, lock/lease clock, and source loader at the public cache boundary so fake-cache tests can prove backend calls, TTL jitter, lock timeout, fallback, and metrics.
- **Permission and policy caches.** PDP TTL must be no longer than propagation SLA and must invalidate on grant change; source must recheck final high-risk actions.
- **HTTP shared cache safety.** Use `private` or `no-store` for sensitive responses, minimize `Vary`, normalize paths, include or strip response-affecting headers, and use surrogate keys for precise purge.
- **Negative cache.** Cache confirmed absence with short TTL, pair with existence filters when the legitimate key set is bounded, and verify transient misses recover.
- **Eviction and memory.** Pick eviction policy to match access skew, alert before `maxmemory`, and measure item size, fragmentation, key cardinality, and p99 latency under pressure.
- **Multi-region and erasure.** Declare replication lag, avoid strong decisions on eventually replicated cache, and invalidate cached PII on erasure.
- **Observability.** Emit hit, miss, stale, bypass, eviction, refresh failure, hot-key, source-load, memory, and `Cache-Status`-style decision signals where applicable.

# Failure Modes

- **Stale correctness:** cache shows revoked permissions, old pricing, deleted records, or cancelled orders.
- **Stampede:** popular key expires; thousands of requests stampede the database simultaneously -> cascading outage.
- **Penetration:** missing-key flood lets attackers force repeated expensive lookups; no negative cache or bloom filter in place.
- **Isolation leak:** cache keys omit tenant or permission scope -> cross-tenant or cross-user data leak when keys collide.
- **Coordinated expiry:** synchronized TTL expiry (no jitter) coordinates a wave of misses every N seconds.
- **Avalanche:** cache cluster restart / failover triggers cold-cache origin meltdown.
- **Web cache deception:** user A's private response is served to user B from a shared CDN.
- **Cache poisoning:** unkeyed header rewrites poison the response served to all subsequent users.
- **Write-behind data loss:** cache loses last-N writes when Redis crashes -> data loss masquerading as cache loss.
- **Hidden hot key:** hit rate looks healthy (e.g., 95%) but a single hot key drives 80% of misses -> invisible source pressure.
- **Mixed schema:** cache value schema rolls out without key versioning; old pods crash on new shape during rolling deploy.
- **Permanent negative:** negative cache without TTL turns transient miss into permanent "not found".
- **Overlong PDP TTL:** permission-decision cache TTL exceeds admin expectation -> revoked admin still acts.
- **Edge cardinality drift:** eviction policy, purge granularity, or `Vary` cardinality mismatch collapses hit rate or spreads stale content globally.
- **Erasure failure:** PII cached beyond erasure SLA creates a privacy and compliance failure.

# Reference Loading Policy

- Use the `SKILL.md` body for L1/L2 routing, stage fit, mode selection, trigger detection, output contract, and quality gate.
- Load [references/checklist.md](references/checklist.md) for concrete cache plans involving distributed caches, HTTP/CDN caches, tenant or permission scoped data, mutable entitlements, pricing, inventory, negative caching, stampede protection, cache-down fallback, or production observability.
- Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when selecting cache pattern/technology, reviewing stampede/penetration/avalanche defenses, handling HTTP cache security, mapping observability and validation evidence, or reconciling graph/memory/execution evidence.
- Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on graph/memory/execution coupling, changed cache-to-validation mapping, stale prior evidence, tool permission boundaries, or final handoff claims.
- Do not load references for isolated request-local memoization with no shared state, no sensitive data, and no stale-read consequence unless the cache behavior is disputed.

# Output Contract

Return a cache strategy with, per cached value class:

- `mode_and_rationale` (request-local, distributed, HTTP/CDN, negative, correctness-sensitive, degradation; why this tier/pattern)
- `source_owner_contract` (source of truth, owner, purpose, consumers, stale tolerance)
- `key_value_contract` (versioned key template, tenant/permission scope, normalized inputs, value schema, serialization, cardinality, max size)
- `freshness_contract` (TTL, jitter, invalidation event/version, consistency window, write-path responsibility)
- `defense_contract` (stampede, penetration, avalanche, hot-key, cold-start, stale-if-error, source backpressure)
- `security_privacy_contract` (secrets/PII redaction, HTTP cacheability, `Vary`, deception/poisoning defenses, erasure path)
- `failure_and_rollout_contract` (cache-down behavior, warm-up, canary, kill switch, rollback independent of cache health)
- `observability_contract` (hit/miss/stale/eviction/refresh-failure/source-load/hot-key/memory metrics, alerts, `Cache-Status`)
- `validation_contract` (tests for stale, miss flood, stampede, cache-down, mixed schema, permission revoke, invalidation race)
- `graph_memory_execution_coupling` (current graph/memory facts used, current files/config/tests/telemetry that confirm or reject them)
- `validation_freshness` (validator/test commands, timestamps or run identifiers, exit code, artifact/report or screenshot path when applicable, and stale evidence called out)
- `tool_permission_boundary` (read-only vs state-mutating cache/tool actions, sandbox, approval requirement, redaction rule)
- `evidence_scope` (what the evidence covers, what remains unproven, residual owner/risk)

# Evidence Contract

A cache change is complete only when the output includes:

- **Boundaries inspected**: cache owner, source of truth, key/value classes, tenant/user/permission scope, HTTP edge boundary, write paths, telemetry, tests, and release path.
- **Selected mode**: cache pattern, tier, and why cheaper alternatives were insufficient.
- **Cache contract**: source of truth, versioned key/value schema, TTL/jitter, invalidation trigger, stale-window acceptance, negative cache policy, memory bound, and eviction policy.
- **Failure behavior**: cache miss, backend unavailable, stampede, stale read, cross-tenant collision, partial invalidation, multi-region lag, and cache-down fallback.
- **Validation evidence**: test or command proving TTL, invalidation, key isolation, stampede protection, negative cache behavior, fallback behavior, and mixed-version safety.
- **Security and privacy review**: tenant/permission scope, key/log redaction, PII erasure, HTTP cacheability, deception, poisoning, and secret handling.
- **Reliability and observability review**: hit/miss/stale/eviction/source-load/hot-key/memory metrics, alert thresholds, drill status, and overload guardrails.
- **What evidence proves**: inspected cache paths stay within declared staleness, isolation, fallback, and observability contracts.
- **What evidence does not prove**: production cardinality, real traffic skew, cache pressure, rare invalidation race, regional propagation delay, or uninspected edge rules.
- **Graph / memory / execution reconciliation**: current repository graph, remembered facts, files, commands, and validation outputs align; stale or missing evidence is named.
- **Reuse / placement rationale**: why cache-specific guidance stays in this capability or its references rather than registry, dist, shared/common, or out-of-scope runtime content paths.
- **Tool boundary**: whether any cache command, purge, telemetry query, build, install, or validation was read-only or state-mutating, with sandbox and redaction noted.
- **Residual risk and handoff**: untested invalidation path, owner, next gate, and handoff target.

# Quality Gate

The strategy passes only when:

1. **Source of truth is named** and cache is explicitly *not* it.
2. **Per cached class**: purpose, key schema (with version + tenant + identity scope), value schema, TTL with jitter, invalidation, consistency tolerance are documented.
3. **Stampede, penetration, and avalanche protection** are designed (not assumed) for hot keys and cold-start.
4. **Tenant + permission scope** is in the key, not in post-fetch filtering.
5. **Cache failure degrades gracefully** under source backpressure; cache-loss drill is executed or scheduled.
6. **Correctness-sensitive caches** use event invalidation/versioning, not TTL guess; schema versioning handles rolling deploys.
7. **HTTP/CDN and privacy review** closes `Cache-Control`, `Vary`, surrogate-key, deception, poisoning, secret, token, PII, and erasure risks.
8. **Observability** covers hit/miss/stale/eviction/source-load/hot-key/memory signals and alert thresholds.
9. **Tests** cover stale, miss flood, stampede, cache-down, mixed-version deploy, permission revoke, and invalidation race.
10. **Rollout** includes warm-up, canary, kill switch, and rollback that does not depend on cache health.
11. **Graph, memory, validation, and tool-boundary evidence** is fresh and records read-only vs state-mutating actions.
12. **Claims are bounded** and do not overstate production traffic skew, regional propagation, memory pressure, or rare races.

# Benchmark Coverage

This capability covers HTTP cache semantics, conditional validation, stale extensions, cache-status observability, distributed cache topology, key namespace isolation, hot-key and stampede defenses, negative cache defenses, CDN purge models, web cache deception and poisoning, rolling schema version safety, cache-down degradation, and observability-driven validation. It does not replace source query optimization, durable storage design, authorization modeling, or deployment rollout ownership.

# Routing Coverage

Route here when cache behavior, freshness, invalidation, or fallback is the central design risk. Combine with `reliability-observability-gate` for overload and degradation, `security-privacy-gate` or `web-security` for shared HTTP cache and tenant/privacy risks, `authentication-authorization` for PDP/permission-decision caches, `indexing-query-optimization` when the real issue is source query cost, `data-model-design` when read shape is wrong, `observability` for signal design, `validation-broker` for evidence freshness, and `agent-tool-permission-sandbox` for cache commands, telemetry reads, validation, build, install, or release actions.

# Used By

- data-middleware-change-builder
- reliability-observability-gate

# Handoff

Hand off to `indexing-query-optimization` when the underlying source query needs to be fixed; `data-model-design` when the read shape requires denormalization; `search-analytics-design` when a specialized read engine is the right answer; `authentication-authorization` for permission-decision cache invalidation; `web-security` / `security-privacy-gate` for HTTP cache deception, poisoning, tenant, or privacy review; `reliability-observability-gate` for degradation policies and overload protection; `observability` for cache-specific signal design; `validation-broker` for evidence freshness; `agent-tool-permission-sandbox` for cache commands and validation/build operations; `backend-change-builder` for implementation.

# Completion Criteria

The capability is complete when **the cache demonstrably accelerates reads within an explicitly bounded staleness budget, never holds the only copy of data, isolates tenants and permissions in the key, defends against stampede / penetration / avalanche, degrades gracefully when the cache itself fails, invalidates correctness-critical values on the write event rather than by TTL guess, exposes hit/miss/stale/source-load signals with alerts, and survives a documented cache-loss drill** — without becoming an uncontrolled source of truth or an outage amplifier.
