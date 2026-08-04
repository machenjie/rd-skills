---
name: non-goal-boundary-definition
description: "`analysis-agent`: use when scope, exclusions, deferred decisions, version limits, or assumptions need explicit boundaries; skip when no task-local non-goal decision is needed."
---

# non-goal-boundary-definition

## Registry Trigger

**Use when**

- separate in-scope work from non-goals exclusions and deferred decisions

**Do not use when**

- no task-local non goal boundary definition decision is required

## Skill Role

Define exclusions, deferred decisions, unchanged behavior, version and environment limits, assumptions, reopen conditions, and observable exclusion evidence. Exclude positive scope and implementation planning.

## High-Value Rules

- **Define exclusions as observable boundaries.** Name the behavior, consumer, data, environment, version, artifact, or operational effect excluded so reviewers can detect accidental inclusion.
- **State reason and authority.** Tie each material non-goal to current request, contract, risk decision, dependency, ownership boundary, or delivery constraint instead of treating convenience as settled scope.
- **Distinguish non-goal, unchanged behavior, deferral, and unknown.** Record which item is intentionally excluded, preserved, postponed with an owner, or unresolved because evidence is missing.
- **Check dependency pressure.** Identify whether in-scope work requires an excluded contract, migration, consumer, security control, cleanup, or operational change; reopen the boundary when exclusion would make the accepted outcome unsafe or incomplete.
- **Attach an exclusion oracle.** Select a review, contract, schema, data, UI, deployment, or behavior check capable of showing the non-goal remained absent, proportional to its consequence.
- **Bound assumptions and versions.** Name supported environments, clients, data states, compatibility windows, and source evidence whose change would invalidate the exclusion.
- **Carry deferred ownership forward.** Record accountable owner, dependency, risk, and reopen signal without turning every possible future enhancement into present scope.

## Anti-Patterns

- Use vague labels such as later, unrelated, unchanged, or out of scope without an observable boundary and reason.
- Exclude required validation, migration, security, rollback, or consumer work while still claiming the positive outcome complete.
- Treat a missing fact as an accepted non-goal or let a deferred item lose ownership and reopen criteria.

## Stop Conditions

Escalate when an exclusion conflicts with accepted behavior, contract, safety, compatibility, or ownership; required dependencies cross the boundary; an assumption lacks authority; or consequential excluded behavior cannot be checked.

## Output Contract

- non-goal boundary with observable exclusions, reasons and authority, unchanged and deferred items, dependencies, assumptions and version limits, exclusion oracles, reopen conditions, and owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | scope exclusions conflict with version compatibility or required controls | approved scope and commitments determine every exclusion | analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | slice needs explicit forbidden surfaces placeholders or deferred decisions | acceptance names testable included and excluded artifacts | analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | out-of-scope not-present or deferred claims need fresh scans | current routes schemas jobs UI and tests prove exclusions | analysis-agent | evidence-record, proof-limit, residual-risk |
