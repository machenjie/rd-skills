---
name: permission-boundary-modeling
description: "`analysis-agent`/`task-agent`/`review-agent`: use for tenant isolation, privilege-escalation, subject-resource-action policy, or enforcement changes; skip authentication-only work."
---

# permission-boundary-modeling

## Registry Trigger

**Use when**

- model subject resource action conditions object tenant scope privilege transitions and enforcement

**Do not use when**

- no task-local permission policy or enforcement decision is required

## Skill Role

Define subject-resource-action-condition decisions, trusted policy inputs, tenant scope, enforcement reachability, bulk semantics, denial disclosure, delegated entitlement, and permission proof. Exclude subject derivation and credential lifecycle.

## High-Value Rules

- **Model the decision and its authorities.** Name subject, resource, action, conditions, decision outcomes, and the current identity, resource, relationship, policy, or lifecycle source authorized to supply each decision input.
- **Resolve object and tenant scope from trusted state.** Derive ownership, tenancy, sharing, classification, and lifecycle from validated identity, resource, relationship, or policy data. Request-supplied selectors remain untrusted, while intentionally public access is recorded as explicit policy.
- **Place enforcement on each reachable protected path.** Require an architecture-appropriate authorization decision before protected data leaves or an effect commits.
- **Define collection and bulk authorization before exposure or effect.** Apply an authoritative visibility predicate before pagination, aggregation, caching, serialization, reporting, or export. The chosen per-object or equivalent aggregate authorization specifies partial-result and continuation behavior.
- **Derive denial disclosure from the current contract.** Distinguish missing identity, invisible resource, visible-but-forbidden action, conditional approval, and unavailable policy state without standardizing one protocol response across resources or clients.
- **Bound delegated and machine entitlement.** Define the resource, action, tenant, run or purpose, delegation source, revocation or end condition, real/effective actor audit, and diagnostic-versus-mutation boundary for service, support, impersonation, and override paths.
- **Prove allows, denials, and bypass resistance.** Cover positive, wrong-subject, wrong-owner, wrong-tenant, stale-relationship, collection, bulk, delegated, and alternate-entry behavior from the changed graph. Uninspected paths, deployed-policy state, and owners remain residual scope.

## Anti-Patterns

- Treat a role, hidden UI control, gateway scope, authenticated caller, or internal workload as the authoritative permission decision for object- or tenant-sensitive work.
- Let caller-controlled owner, tenant, role, status, purpose, or mutable privilege fields establish entitlement, or filter a broad result after protected data has crossed its disclosure boundary.
- Generalize one endpoint’s denial response, one policy placement, or one happy-path fixture to unrelated resources, entry points, bulk behavior, delegated actors, or deployed policy state.

## Stop Conditions

Escalate when a policy input lacks trusted authority, a protected path lacks reachable enforcement, shared or cross-tenant scope is ambiguous, or bulk semantics can expose unauthorized objects. Also escalate when delegated mutation lacks attribution or end conditions, denial conflicts with the public contract, or residual paths lack an owner.

## Output Contract

- permission contract with authoritative decision inputs, subject-resource-action conditions, object and tenant scope, reachable enforcement, collection and bulk semantics, denial disclosure, delegated entitlement, negative proof, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | competing object relationship context collection bulk delegation denial or placement patterns remain viable | current policy and enforcement path resolve the changed permission decision | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | several permission matrix enforcement collection bulk denial delegation or rollout decisions must close together | one bounded permission decision is already complete from the root contract | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | authority scope enforcement collection bulk denial delegation rollout or negative-path claims need fresh proof | current source and selected fixtures prove the bounded permission claims | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
