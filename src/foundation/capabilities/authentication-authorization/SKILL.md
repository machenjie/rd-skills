---
name: authentication-authorization
description: "`analysis-agent`/`task-agent`/`review-agent`: use for authenticated-subject authority, propagation, or authorization handoff changes; skip credential lifecycle or policy-only work."
---

# authentication-authorization

## Registry Trigger

**Use when**

- define authenticated subject authority derivation propagation and authentication-to-authorization context handoff

**Do not use when**

- no task-local authenticated-subject authority propagation or authorization-handoff decision is required

## Skill Role

Define authenticated-subject authority, derivation, propagation, real/effective actor attribution, downstream context freshness, and the authorization handoff. Exclude credential lifecycle and subject-resource-action policy.

## High-Value Rules

- **Name the authenticated-subject authority and semantics.** Distinguish human, workload, partner, delegated, real, and effective actors; state which current source can assert each subject and which caller fields are untrusted.
- **Derive the internal subject at a trusted boundary.** Map accepted authentication to one internal identity and tenant context with explicit ambiguous-account failure behavior.
- **Preserve provenance through propagation.** Carry actor kind, real/effective relationship, authority, bindings, authentication source, and unresolved context across API/RPC, worker/consumer, callback, admin, and support boundaries. Downstream callers cannot rewrite that provenance.
- **Bound freshness for downstream permission context.** Define authoritative re-resolution or failure behavior for identity, membership, delegation, tenant, or assurance changes.
- **Keep the authorization handoff explicit.** Pass authenticated subject, provenance, tenant context, relevant assurance state, and freshness limits without treating identity proof, embedded roles, groups, or scopes as permission to perform an action.
- **Preserve attribution for delegated and machine actors.** Record real and effective subject, delegation source, credential owner, workload purpose, and audit identity without redefining credential or entitlement policy.
- **Prove reachable derivation and handoff failures.** Test scoped identity paths against applicable failure contexts, recording unknown or externally owned paths.

## Anti-Patterns

- Treat an authenticated session, signed assertion, embedded role, or internal caller as sufficient authorization for a protected action.
- Trust caller-supplied subject, tenant, delegation, role, group, or scope, or propagate identity context whose authority and freshness cannot be reconstructed downstream.
- Expand this Skill into credential/session/token control selection, or generalize one successful login or API path to workers, callbacks, recovery, support, and external identity mappings.

## Stop Conditions

Escalate when subject authority or real and effective attribution is ambiguous, or multiple upstream identities cannot resolve to one owned internal subject. Also escalate when handed-off tenant or delegation context is caller-controlled, downstream freshness is unbounded, provenance can be overwritten, or an unknown path lacks an accountable owner.

## Output Contract

- authenticated-subject authority and handoff contract with trusted derivation, actor provenance, propagation boundaries, downstream freshness, authorization context, negative proof, unverified paths, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | competing subject-authority derivation propagation attribution freshness or handoff patterns remain viable | current identity authority and propagation graph resolve the changed handoff decision | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | several subject propagation attribution freshness handoff or reachability decisions must close together | one bounded authenticated-subject decision is already complete from the root contract | task-agent, analysis-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | subject authority derivation propagation attribution freshness handoff reachability or negative-path claims need fresh proof | current source and selected fixtures prove the bounded authenticated-subject claims | task-agent, analysis-agent, review-agent | evidence-record, proof-limit, residual-risk |
