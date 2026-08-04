# Cache Design Evidence Patterns

Use this reference when cache closure depends on current source, prior claims, validation freshness, or tool boundaries. Include only cache claims and failure paths triggered by current topology and stale/source-load risk; mark accepted unexecuted checks `planned`/`not_run` with reason. Keep it as an evidence map.

## Cache-To-Validation Map

| Cache claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Source of truth remains authoritative | Current write path, source owner, and cache population path inspected | Cache loss cannot lose durable state for inspected class | Uninspected write-behind paths or manual repair scripts |
| Tenant and permission isolation is enforced | When identity affects the value: selected key dimension, namespace, dedicated cache/partition, or other enforced boundary plus focused denial/cross-scope proof | The inspected cache boundary cannot reuse another actor's value | Every future representation or CDN rule is safe |
| TTL and invalidation are bounded | When freshness matters: stale budget plus selected TTL/version/event/purge path and focused ordering proof | Freshness window is explicitly owned | Rare invalidation races or regional propagation delay |
| Stampede control works | When contention risk exists: selected coalescing/lease/source-limit behavior plus focused concurrency evidence at its claimed process/pod scope | The selected control bounds refresh work for the tested scope | Real traffic skew, pod count, Redis latency, or source capacity |
| Cache-down fallback is bounded | When cache loss can overload or fail the source: failure behavior, source-protection rule, and focused proof | Inspected fallback follows the selected availability/source-load policy | Production source can absorb full cold-cache traffic |
| Negative cache recovers | When negative caching or filtering is selected: transient-miss recovery proof using the selected expiry, invalidation, version, purge/revalidation, or filter refresh/bypass mechanism | False absence does not become permanent | Adversarial key-space volume beyond tested rate |
| HTTP/CDN cache is private-safe | When shared/edge caching applies: response classification and only applicable cache-key/namespace, `Cache-Control`, `Vary`, surrogate/tag, purge/revalidation, and deception/poisoning evidence | The inspected edge boundary does not store personalized content publicly | Other routes, inherited CDN rules, or proxy rewrites |
| Mixed schema rollout is safe | Versioned key/value schema review plus old/new reader test or migration note | Rolling deploy does not mix incompatible shapes for inspected class | Old clients outside the tested deployment set |
| Triggered degradation is observable | Metrics and alert ownership selected only for triggered stale, eviction, source-load, hot-key, cardinality, or memory risks and their owned action | Operators can see the inspected cache risk and response signal | Alert thresholds are perfect under production seasonality |

## Current Evidence And Freshness

- Treat repository inspection, previous skill runs, issue history, runbooks, dashboards, and old validation reports as selectors for inspection, not proof.
- Accept a prior cache claim only when the key schema, TTL, invalidation path, permission model, serialization version, topology, and validation command still match the current source.
- Mark evidence stale after material edits to cache keys, value schema, TTL, invalidation events, permission filters, edge rules, deployment topology, fixtures, validators, or build/install outputs.
- Record the current inspected paths and skipped paths. A focused cache validation can close a local skill edit, but it does not certify production Redis, CDN, or telemetry behavior.
- Map each triggered claim to current source or existing artifacts and, when a permitted check ran, its result. Otherwise record `planned`/`not_run`, reason, owner, and residual risk.

## Tool Permission Boundary

- Cache writes, flushes, purges, and CDN invalidations require an authorized namespace, bounded key or rate scope, stop condition, and a rebuild or rollback path.
- For production cache telemetry or diagnostics, prefer metadata, redact sensitive cached values, and qualify cache-health conclusions with tiers, replicas, or stale objects outside the observation scope.

## Handoff Evidence Shape

```yaml
cache_evidence:
  profile: task-agent | review-agent
  inspected_paths:
    - path: ""
      evidence_and_freshness: ""
  prior_claims:
    - claim: ""
      verdict_and_evidence: ""
  cache_to_validation:
    - cache_decision: ""
      status: planned | ran | not_run
      evidence_or_reason: ""
      proves_and_limits: ""
  mutation:
    action_or_none: ""
    authority_cleanup_redaction: ""
  residual_risk:
    - risk: ""
      owner_or_gate: ""
```
