---
name: cache-design
description: "Use with task-agent or review-agent for task-local cache scope, freshness, invalidation, and source-load risk. Do not use without a cache decision or as task owner."
---

# cache-design

## Registry Trigger

**Use when**

- design cache keys TTL invalidation stampede protection and freshness policy
- Redis ElastiCache Cloud Memorystore Memcached Redis Cluster Redis Sentinel Redis ACL RDB AOF maxmemory eviction hot key pipeline cache stampede cache penetration cache avalanche

**Do not use when**

- no task-local cache design decision is required

## Skill Role

Protect cache correctness, scope isolation, freshness, failure behavior, and source capacity.

## High-Value Rules

- Name the source of truth, owner, acceptable staleness, value/key version, and tenant/user/permission scope before caching; cache loss must not silently change correctness or expose another scope.
- Model process/pod/region topology, key popularity, expiry distribution, cold start, miss rate, and origin capacity. Single-flight, leases, jitter, early refresh, stale serving, negative caching, warm-up, or origin limiting are candidates selected from the available evidence.
- Define freshness-required invalidation at the actual write or commit boundary.
- Define cache-down, refresh-failure, stale-data, eviction, and source-overload behavior.
- Require explicit durability and recovery proof for write-behind.

## Anti-Patterns

- In-process request coalescing does not prevent a cross-pod stampede, and coordinated expiry can overload the source even with a high historical hit rate.
- Do not treat TTL as invalidation for permissions, prices, balances, inventory, or other correctness-sensitive values.
- Scope shared and edge cache keys to prevent personalized data from crossing user or tenant boundaries.

## Execution Checklist

1. Map source, writers, readers, least-tolerant consumer, key scope, value shape, invalidation events, and failure modes.
2. Estimate hot-key, miss-storm, coordinated-expiry, restart/failover, and stale-serve impact against measured topology and origin capacity, then select only justified controls.
3. Validate every remaining triggered cache risk.
4. Record unavailable checks and their proof limits.

## Stop Conditions

- Escalate permissions, financial state, pricing, inventory, compliance/audit data, multi-tenant edge caching, write-behind, cross-region caches, or origin-overload risk when stale tolerance, scope, durability, or recovery ownership is unclear.

## Output Contract

- cache strategy with keys freshness invalidation and fallback behavior

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Read/write pattern, invalidation, fallback, or load protection remains open | No cache topology or source-load decision changes | task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Cache behavior spans scope collisions, staleness, outages, or hot keys | The cache is absent from the affected correctness path | task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Cache safety claims need current topology and failure-path tests | No freshness, isolation, or source-load claim needs proof | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
