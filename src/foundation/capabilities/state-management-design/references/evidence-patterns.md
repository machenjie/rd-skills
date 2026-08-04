# State Management Design Evidence Patterns

Use this reference when state-management closure depends on state-to-validation mapping, auth/cache clearing proof, browser persistence evidence, optimistic rollback proof, stale store memory, or proof limits. Keep it as an evidence map, not a framework catalog.

## State Surface-To-Validation Map

| State claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Source of truth is singular | State inventory, owner path, readers/writers, rejected duplicate storage, and reset or invalidation rule | Inspected value has one declared authority and lifecycle | Future components or hidden persistence cannot duplicate it |
| Server cache is coherent | Query key, freshness/retention, invalidation trigger, stale display behavior, and mutation test or review | Inspected cache path can refresh or reset under named conditions | Production cache pressure or all backend changes are covered |
| Auth state clears safely | Trusted identity source, 401/logout/role-change path, cache/storage clear checklist, and test or review | Inspected protected state clears for named auth transitions | Deployed IdP behavior or every tab/browser variant is proven |
| Persisted browser state is bounded | Stored key, sensitivity class, per-user keying, expiry, clear-on-logout rule, and privacy review | Inspected persisted state has retention and privacy controls | XSS, browser extension, or older release storage is fully mitigated |
| Optimistic mutation can recover | Pre-mutation snapshot, rollback trigger, server confirmation, conflict handling, and failure test | Inspected mutation can recover from rejection or conflict | Server idempotency or all race branches are proven |
| Prior store/cache pattern is fresh | Current store/hook/query/auth paths, accepted/rejected memory, validator/report, and final-edit freshness | Reused pattern still matches inspected source | Later store, route, cache, or auth edits remain covered |

## Evidence Quality Labels

- **Strong evidence**: current store/hook/query/auth/persistence/test paths inspected, command or review artifact named, final-edit freshness stated, and proof limits named.
- **Weak evidence**: "use React Query" statement, framework default citation, old prior task evidence, happy-path component test, or graph proximity.
- **Missing evidence**: no state inventory, no cache invalidation map, no logout/401 clearing proof, no persisted-key classification, no optimistic rollback test, or no residual owner.
- **Invalid evidence**: client-writable permission treated as authority, sensitive token in localStorage without security decision, copied server truth with no invalidation, or stale store memory accepted as proof.

## Tool Permission Boundary

- Live auth/session tests, feature-flag changes, and browser credential mutations require an authorized environment, test identity, stop condition, rollback path, and credential redaction.
- When production state telemetry supports a state-management conclusion, record the store or query scope, freshness, applicable tenant dimensions, and the client or server states that remain unobserved.

## Handoff Evidence Shape

```yaml
state_management_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  state_surface_to_validation_map:
    - surface: ""
      risk: source_of_truth | cache | auth | persistence | optimistic | freshness
      validator_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
  tool_permission_boundary:
    action_class: ""
    state_mutation: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
