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

Own subject authority and authorization handoff; exclude credential lifecycle and permission policy.

## High-Value Rules

- Define subject authority, provenance, attribution, and freshness from current evidence.
- Preserve handoff context for its permission owner to decide action.
- Select one active named Reference.

## Anti-Patterns

- Local success is insufficient.

## Stop Conditions

Stop on ambiguous, caller-controlled, stale, overwritable, unowned, or unproved authority or handoff.

## Output Contract

- authenticated-subject authority and handoff contract with trusted derivation, actor provenance, propagation boundaries, downstream freshness, authorization context, negative proof, unverified paths, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | competing subject-authority derivation propagation attribution freshness or handoff patterns remain viable | current identity authority and propagation graph resolve the changed handoff decision | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | several subject propagation attribution freshness handoff or reachability decisions must close together | one bounded authenticated-subject decision is already complete from the root contract | task-agent, analysis-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | subject authority derivation propagation attribution freshness handoff reachability or negative-path claims need fresh proof | current source and selected fixtures prove the bounded authenticated-subject claims | task-agent, analysis-agent, review-agent | evidence-record, proof-limit, residual-risk |
