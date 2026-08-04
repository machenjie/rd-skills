# Permission Boundary Modeling Benchmarks And Patterns

Load this reference when object, relationship, context, collection, bulk, delegation, denial, or enforcement-placement semantics leave multiple viable patterns. Do not load it for identity, credential, session, or token lifecycle decisions alone.

## Permission Decision Patterns

| Decision shape | Compare | Required proof |
| --- | --- | --- |
| Object or tenant scope | Ownership, tenancy, classification, lifecycle, sharing, or explicit public policy | Trusted attribute authority, subject-resource relationship, changed paths, and wrong-scope cases |
| Relationship or inheritance | Direct grant, group or hierarchy, delegated relation, inherited visibility, or bounded resource grants | Relationship writer, consistency and deletion behavior, traversal boundary, stale case, and owner |
| Context-sensitive permission | Current subject, resource, environment, assurance, purpose, or workflow state | Attribute authority and freshness, evaluation path, unavailable-state behavior, and negative cases |
| Collection or derived view | Source predicate, permission-aware index or materialization, or bounded post-processing that cannot cross the disclosure boundary | Pagination/count/cache/export behavior, update lag, stale-result handling, and cross-scope fixture |
| Bulk action | Per-object decision, equivalent aggregate predicate, or an explicitly bounded homogeneous set | Mixed-scope input, partial-result or atomic behavior, continuation or retry semantics, and audit |
| Delegated or machine entitlement | Direct workload policy, bounded delegation, support or impersonation rule, or controlled override | Resource/action/tenant/run or purpose scope, real/effective actor, end condition, and misuse case |

## Enforcement, Denial, And Change

- Place the authoritative decision before the protected disclosure or effect on each reachable path. Choose controller, service, repository/query, worker, policy service, gateway, or multiple layers according to the actual architecture and bypass analysis.
- Derive unauthenticated, invisible-resource, forbidden-action, conditional, and policy-unavailable outcomes from the current disclosure and failure contract while retaining their distinction through in-scope gateways, SDKs, jobs, and clients.
- Compare old and new allow/deny behavior during policy rollout, stale-policy or relationship windows, partial deployment, rollback, and legitimate-access regression.
- Audit the real/effective actor, resource, action, decision, stable reason or policy version, scoped context, and approved purpose without secrets or unnecessary sensitive data.

## Proof Limits

Scoped source and negative tests prove the inspected paths and policy data represented by fixtures. They do not establish unknown entry points, deployed grants or relationship tuples, external consumers, production propagation, or human approval compliance unless those surfaces are independently verified.
