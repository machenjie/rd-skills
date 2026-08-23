---
name: design-pattern-selection
description: "`analysis-agent`/`task-agent`/`review-agent`: use when a current variation, lifecycle, protocol, or concurrency force may justify a pattern; skip pattern-name or placement work."
---

# design-pattern-selection

## Registry Trigger

**Use when**

- Current construction variants, algorithm choices, state transitions, event fan-out, protocol translation, lifecycle, or extension forces need a relationship decision.
- A proposed abstraction can hide I/O, global state, concurrency, teardown, compatibility, or invariant enforcement.

**Do not use when**

- A pattern name merely appears, or direct local structure resolves the force with no unresolved object relationship.
- The decision is placement, behavior-preserving movement, language semantics, performance, or public API shape without a pattern choice.

## Skill Role

Select one relationship for an accepted variation, lifecycle, protocol, concurrency, or extension force; exclude placement, refactoring, public contracts, and language rules.

## High-Value Rules

- Define the current force, reachable consumers, and direct alternative.
- Define construction, lifecycle, effect, concurrency, and failure ownership.
- Preserve visible I/O, latency, failure, cancellation, cleanup, and results; sharing is not a force.
- Route public/cross-module surfaces and specialist proof.

## Anti-Patterns

- Local success substituted for evidence of the design pattern selection contract.

## Stop Conditions

- Consume accepted structure; hand relationship placement/movement and specialist proof to their owners.

## Output Contract

- pattern decision with current forces, selected or rejected relationship, simpler direct alternative, construction/lifecycle/effect obligations, evidence and proof limits, specialist handoffs, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [pattern evidence record](references/pattern-evidence-record.md) | evidence-pattern | A design-pattern candidate needs current-force repository-fit lifecycle IO concurrency or compatibility evidence | No design pattern is selected or direct local structure already resolves the current force | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
