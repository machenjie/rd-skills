# Permission Boundary Modeling Checklist

- Identify subjects, resources, actions, conditions, decisions, and the authoritative source for each policy input.
- Map ownership, tenant, sharing, classification, lifecycle, and intentionally public access for the changed resources.
- Mark caller-controlled owner, tenant, role, status, purpose, or privilege fields and the trusted state used by the decision.
- Map protected API, RPC, worker, consumer, callback, import, admin, support, repository/query, cache, report, and export paths in scope to enforcement before disclosure or effect.
- Define collection visibility before pagination, count, aggregation, caching, serialization, reporting, and export.
- Define bulk per-object or equivalent aggregate authorization plus partial-result, atomicity, continuation, retry, and audit behavior.
- Derive missing-identity, invisible-resource, forbidden-action, conditional, and unavailable-policy outcomes from the current contract.
- Bound service, support, impersonation, delegation, and override resource/action/tenant/run or purpose scope, end condition, and real/effective actor audit.
- Compare old and new allow and deny behavior across policy or relationship rollout, staleness, partial deployment, and rollback.
- Select applicable positive, wrong-subject, wrong-owner, wrong-tenant, stale-relationship, collection, bulk, delegated, and alternate-entry cases.
- Record unknown paths, deployed policy or relationship state, external consumers, propagation, and human-process compliance as residual scope with owners.
