# Cache Design Evidence Patterns

Use this reference when cache closure depends on current graph, memory, execution output, validation freshness, or tool permission boundaries. Keep it as an evidence checklist, not a second cache tutorial.

# Cache-To-Validation Map

| Cache claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Source of truth remains authoritative | Current write path, source owner, and cache population path inspected | Cache loss cannot lose durable state for inspected class | Uninspected write-behind paths or manual repair scripts |
| Tenant and permission isolation are in the key | Key template plus denied/cross-tenant test or review artifact | Inspected key class cannot reuse another actor's value | Every future representation or CDN rule is safe |
| TTL and invalidation are bounded | TTL/jitter rule plus write-event, version-key, outbox, CDC, or purge path | Freshness window is explicitly owned | Rare invalidation races or regional propagation delay |
| Stampede control works | Deterministic fake-cache concurrent same-key test with backend calls equal to one | Local refresh coalescing or lease behavior works for the tested path | Real traffic skew, pod count, Redis latency, or source capacity |
| Cache-down fallback is bounded | Fake Redis-unavailable or cache-client failure test plus source backpressure rule | Application does not fail solely because cache is unavailable | Production source can absorb full cold-cache traffic |
| Negative cache recovers | Transient miss test with short TTL or existence filter behavior | False absence does not become permanent | Adversarial key-space volume beyond tested rate |
| HTTP/CDN cache is private-safe | Header sample, `Cache-Control`, `Vary`, surrogate-key, purge, and deception/poisoning test | Inspected edge rule does not store personalized content publicly | Other routes, inherited CDN rules, or proxy rewrites |
| Mixed schema rollout is safe | Versioned key/value schema review plus old/new reader test or migration note | Rolling deploy does not mix incompatible shapes for inspected class | Old clients outside the tested deployment set |
| Observability can catch degradation | Hit/miss/stale/eviction/source-load/hot-key/memory metrics and alert owner | Operators can see inspected cache decisions and overload symptoms | Alert thresholds are perfect under production seasonality |

# Graph, Memory, And Execution Reconciliation

- Treat repository graph, previous skill runs, issue history, runbooks, dashboards, and old validation reports as selectors for inspection, not proof.
- Accept a prior cache claim only when the key schema, TTL, invalidation path, permission model, serialization version, topology, and validation command still match the current source.
- Mark evidence stale after material edits to cache keys, value schema, TTL, invalidation events, permission filters, edge rules, deployment topology, fixtures, validators, or build/install outputs.
- Record the current inspected paths and skipped paths. A focused cache validation can close a local skill edit, but it does not certify production Redis, CDN, or telemetry behavior.
- Map every final claim to a command, test, validator, report, screenshot, or manual artifact with exit code or explicit not-run status.

# Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, `rg`, `find`, parser scripts | Read-only local shell action; cite searched paths and avoid dumping full output |
| Local validators and builds | State-mutating only for reports/dist/build artifacts; cite log path and exit code |
| Cache flush, purge, Redis CLI write, CDN invalidation | State-mutating runtime action; require permission, dry-run when available, rollback/rebuild path, and owner |
| Telemetry query or dashboard export | Read-only or connector-scoped; redact tenant/user/secret-bearing labels and aggregate sensitive samples |
| Production diagnostic or load command | Risky operation; record sandbox, target environment, rate limit, stop condition, rollback, and redaction rule |

# Handoff Evidence Shape

```yaml
cache_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_cache_to_validation_map:
    - cache_decision: ""
      validator_or_test: ""
      exit_code: ""
      artifact_or_report: ""
      proves: ""
      does_not_prove: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
