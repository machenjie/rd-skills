---
name: dependency-wiring-lifecycle
description: "`analysis-agent`/`task-agent`/`review-agent`: use when construction, injection, lifecycle scope, clients, overrides, or shutdown ownership changes; skip unaffected wiring."
---

# dependency-wiring-lifecycle

## Registry Trigger

**Use when**

- dependency wiring lifecycle
- dependency wiring lifecycle checks
- dependency wiring lifecycle composition root constructor injection factory provider service locator lifecycle scope singleton reusable client pool startup validation shutdown cleanup test override circular dependency configuration driven wiring

**Do not use when**

- no task-local dependency wiring lifecycle decision is required

## Skill Role

Define construction authority, dependency direction, lifetime scope, context propagation, startup and shutdown, reusable resource ownership, test overrides, and wiring evidence. Exclude package selection and architecture boundaries.

## High-Value Rules

- **Keep construction at an owned composition boundary.** Separate object creation, configuration resolution, resource acquisition, and application behavior so domain code does not locate ambient dependencies.
- **Match lifetime to state and concurrency semantics.** Define process, request, job, tenant, transaction, thread or task, and operation scope from mutable state, safety, reuse, cleanup, and isolation needs.
- **Propagate context without ambient mutation.** Carry cancellation, deadline, identity, tenant, transaction, trace, and configuration through explicit owned boundaries, preserving provenance and preventing cross-request leakage.
- **Own reusable clients and pools.** Define construction, sharing, refresh, health, credential and endpoint changes, connection lifecycle, shutdown, and metrics according to the underlying library contract.
- **Make startup and shutdown dependency-aware.** Validate required configuration and connectivity at the appropriate boundary, order acquisition and release, drain in-flight work, and expose partial-start or failed-shutdown behavior.
- **Keep test overrides bounded and equivalent.** Replace dependencies through the same composition contract, preserve material lifecycle and failure semantics, and prevent test-only wiring from becoming a production bypass.
- **Detect cycles and hidden construction.** Trace factories, providers, callbacks, lazy initialization, global registries, and framework hooks, then prove the changed graph and lifecycle with focused startup, concurrency, and cleanup evidence.

## Anti-Patterns

- Construct network clients, pools, or stateful collaborators inside hot operations without explicit lifetime and cleanup ownership.
- Use a service locator or mutable global to hide dependency, tenant, transaction, or test override boundaries.
- Treat successful startup as proof that refresh, concurrent use, partial failure, drain, and shutdown are correct.

## Stop Conditions

Escalate ambiguous construction, cross-trust lifetime leaks, unowned refresh or shutdown, ordering-based cycle workarounds, or unproved test/production wiring equivalence.

## Output Contract

- dependency-wiring decision with composition authority, graph direction, lifetime and context scope, reusable-resource ownership, startup and shutdown behavior, override fidelity, evidence limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Construction ownership, lifecycle scope, or provider patterns remain open | Existing composition roots already own the changed dependency | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Wiring changes clients, pools, shutdown, cancellation, or test overrides | No dependency edge or resource lifecycle changes | task-agent, review-agent, analysis-agent | checklist-result, validation-plan |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Lifecycle claims require fresh graph, startup, or cleanup proof | No reuse, scope, or shutdown claim needs validation | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
