---
name: state-management-design
description: "Use for client state ownership across local, server, optimistic, persisted, form, auth, or cache boundaries."
---

# state-management-design

## Registry Trigger

**Use when**

- A state-ownership or lifetime decision is active.

**Do not use when**

- Skip work without a task-local state-management decision.

## Skill Role

Own state authority, identity, scope, transitions, persistence, cleanup, and evidence; exclude backend lifecycle, cache architecture, and permissions.

## High-Value Rules

- **Classify state.** Define authority, lifetime, and scope.
- **Bind ownership.** Define freshness keys from consumer and identity boundaries.
- **Close transitions.** Define async, optimistic, persistence, and cleanup behavior.

## Anti-Patterns

- Local success is not state-management contract proof.

## Stop Conditions

Stop on ambiguous authority, cross-identity state, unowned persistence, or unverified cleanup.

## Output Contract

- state-management decision with classification, authority and scope, identity and freshness, async and optimistic behavior, persistence policy, cleanup evidence, proof limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | state ownership storage freshness invalidation or persistence choices remain unresolved | one authoritative owner determines storage lifecycle and reset behavior | task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | change affects server UI form auth derived or persisted state | local state edit preserves ownership lifetime and synchronization | task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | invalidation logout rollback or persistence claims need fresh proof | current stores hooks fixtures and tests prove each claim | task-agent | evidence-record, proof-limit, residual-risk |
