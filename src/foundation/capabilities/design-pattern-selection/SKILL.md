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

After `minimal-correct-implementation` has established that structure is needed, select or reject inheritance, composition, strategy, adapter, provider, interface, registry, or another pattern only for a current variation, lifecycle, protocol, concurrency, or extension force. Exclude placement, refactoring, public contracts, and language rules.

## High-Value Rules

- Name the current variation, lifecycle, protocol, concurrency, or extension force, reachable variants or consumers, and the simpler direct alternative before selecting a pattern.
- The selected relationship exposes construction, lifecycle and teardown ownership, dependency direction, invariant enforcement, and side-effect visibility.
- An interface, registry, provider, or base type has a current substitution axis, independent boundary contract, or lifecycle need; shared implementation by itself is not a force.
- An adapter, proxy, repository, decorator, or facade keeps latency, partial failure, timeout, retry, cancellation, and cleanup obligations visible at the call site or owning boundary.
- When selecting a singleton, pool, observer, subscription, or worker, define initialization, synchronization, reset, unsubscribe or drain, shutdown, and error ownership.
- A queue, pool, pipeline, observer, or fan-out relationship defines work bounds, overload behavior, cancellation, teardown, and result or failure observation.
- A public, generated, serialized, or cross-module surface change routes to the API, consumer-impact, module, or compatibility owner before pattern approval.

## Anti-Patterns

- A factory, builder, strategy, registry, or provider wraps one trivial local variant and adds no independent contract or lifecycle.
- A pattern name hides mutable global state, network or storage I/O, commit order, or cleanup work.
- A base type exists for code sharing while callers depend on subtype details or one unstable axis.
- A familiar repository pattern is copied without proving the same force, lifetime, and failure boundary.

## Stop Conditions

- Consume the accepted existence decision from `minimal-correct-implementation`; do not repeat its delete/reuse/native/direct/new ladder.
- After the relationship is accepted, route owner-internal method/class/file placement to `implementation-structure-design`, cross-owner/public edges to `module-boundary-design`, and later behavior-preserving movement to `refactoring`.
- Route language/runtime semantics to `language-idiom-enforcement`, runtime cost to `language-performance-safety` or `profiling`, and concurrency or lifecycle proof to their specialist owners.

## Output Contract

- pattern decision with current forces, selected or rejected relationship, simpler direct alternative, construction/lifecycle/effect obligations, evidence and proof limits, specialist handoffs, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [pattern evidence record](references/pattern-evidence-record.md) | evidence-pattern | A design-pattern candidate needs current-force repository-fit lifecycle IO concurrency or compatibility evidence | No design pattern is selected or direct local structure already resolves the current force | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
