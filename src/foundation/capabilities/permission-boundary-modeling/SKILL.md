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

Own permission authority, scope, enforcement, collection, bulk, denial, delegation, and negative proof; exclude identity and credential lifecycle.

## High-Value Rules

- Resolve decision inputs from trusted identity, resource, relationship, policy, or lifecycle state.
- Enforce the decision before protected disclosure or effect on each in-scope path.
- Load the named benchmark, checklist, or evidence Reference according to the open output.

## Anti-Patterns

- Do not infer permission from authentication, UI hiding, gateway scope, internal callers, or caller fields.

## Stop Conditions

- Stop on untrusted authority, unreachable enforcement, ambiguous scope, unsafe collection or bulk behavior, unbounded delegation, incompatible denial, or unowned paths.

## Output Contract

- permission contract with authoritative decision inputs, subject-resource-action conditions, object and tenant scope, reachable enforcement, collection and bulk semantics, denial disclosure, delegated entitlement, negative proof, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | competing object relationship context collection bulk delegation denial or placement patterns remain viable | current policy and enforcement path resolve the changed permission decision | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | several permission matrix enforcement collection bulk denial delegation or rollout decisions must close together | one bounded permission decision is already complete from the root contract | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | authority scope enforcement collection bulk denial delegation rollout or negative-path claims need fresh proof | current source and selected fixtures prove the bounded permission claims | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
