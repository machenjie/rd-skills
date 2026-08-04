---
name: user-flow-modeling
description: "`analysis-agent`/`task-agent`: use when actor journeys change entries, branches, interruption, recovery, authority, or side effects; skip route/state-only work."
---

# user-flow-modeling

## Registry Trigger

**Use when**

- A named actor journey changes its goal, starting state, preconditions, reachable entries, branches, exits, interruption, recovery, authority disclosure, or side-effect outcome.
- Navigation, refresh, cancellation, timeout, async completion, duplicate action, or unknown result can alter what the actor sees or what the system has committed.

**Do not use when**

- The open decision is content grouping, route implementation, one interaction state, visual composition, or an unordered scenario inventory.
- No actor goal, precondition, journey branch, recovery, authority, or side-effect outcome changes.

## Skill Role

Model ordered journeys through actor goal, preconditions, reachable entries, branch outcomes, interruption, re-entry, user-visible authority, side-effect states, and asynchronous recovery.

## High-Value Rules

- Define the actor, goal, starting state, preconditions, and every reachable entry.
- Define observable branch predicates with both user-visible and system outcomes.
- State what each relevant exit shows, persists, leaves unknown, and permits next.
- Define interruption, refresh, expiry, re-entry, input retention, sensitive cleanup, and focus behavior.
- Distinguish side-effect initiation, commit, unknown result, duplicate attempt, retrieval, partial completion, and compensation.
- Separate user disclosure and recovery from backend authority.
- Cover timeout, away, failure, return, and notification outcomes when work outlives the view.

## Anti-Patterns

- A happy path is complete while direct entry, interruption, unknown outcome, partial completion, or re-entry remains implicit.
- Input or draft preservation and sensitive-value cleanup are selected by convention without a current owner and lifecycle rule.
- Retry, back, refresh, or duplicate actions can replay a side effect, while the flow invents a client key or transport status instead of routing the contract.
- Hidden, disabled, or omitted UI is presented as authorization, or denial reveals protected state without a disclosure decision.

## Stop Conditions

- Stop fail-closed only when an applicable fact decisive to the changed journey is unknown or unavailable.
- Accept evidence-backed non-applicability for authority or disclosure ownership, downstream consumers, and side effects.
- Treat missing journey-validation evidence as blocking only when it could change the selected branch or recovery or re-entry behavior.
- Do not select branch or recovery behavior from assumptions.
- Route actor, scenario, information, route, and view-state decisions to their specialist owners.
- Route authorization, duplicate handling, effects, implementation, acceptance, and proof to their specialist owners.

## Output Contract

- user-flow decision with actor goal preconditions entries predicates exits interruptions recovery authority side effects proof limits and specialist routes

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Journey entries branches interruptions permission side effects or async recovery have competing outcomes or unclear proof | Current flow predicates system outcomes recovery contracts and focused tests settle the changed journey | analysis-agent, task-agent | option-comparison, selected-approach |
