---
name: dependency-wiring-lifecycle
description: Governs dependency construction, injection, lifecycle scope, composition roots, reusable client ownership, startup validation, test overrides, and shutdown cleanup for services, jobs, adapters, and modules.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "108"
changeforge_version: 0.1.0
---

# Mission

Make dependency graphs explicit, acyclic, testable, and resource-safe by deciding where dependencies are created, how they are injected, how long they live, and who shuts them down.

# When To Use

Use when adding or changing constructors, factories, providers, dependency injection containers, composition roots, service clients, DB pools, Redis/Kafka/HTTP/SDK clients, schedulers, timers, subscriptions, sockets, file handles, or test overrides.

Use when per-operation client construction, service locator access, global mutable state, circular dependency, lazy initialization, startup validation, or shutdown cleanup is unclear.

# Do Not Use When

Do not use for pure functions or data-only DTO changes with no collaborators or resources.

Do not use to introduce a dependency injection framework where direct construction in the existing composition root is simpler and local convention supports it.

# Non-Negotiable Rules

- Dependencies are created at the narrowest correct lifecycle scope.
- External clients and pools are not constructed per operation.
- Service locator is rejected unless framework convention requires it and tests can control it.
- Global mutable state needs ownership, synchronization, reset, and shutdown.
- Every long-lived dependency has startup validation and cleanup.
- Dependency graph must be acyclic or explicitly justified.
- Test overrides must not alter production wiring semantics.

# Industry Benchmarks

Anchor against composition root practice, constructor injection, dependency inversion, twelve-factor config binding, framework lifecycle hooks, connection pooling guidance, graceful shutdown practice, resource leak detection, and architecture dependency graph checks.

# Selection Rules

Select this capability over `implementation-structure-design` when the primary decision is dependency graph or lifecycle rather than file placement. Use it with `language-performance-safety` for clients, pools, timers, subscriptions, sockets, and descriptors. Use it with `configuration-runtime-policy` when config drives wiring. Use it with `testability-seam-design` when test overrides require seams.

# Risk Escalation Rules

Escalate to `architecture-impact-reviewer` when wiring changes module boundaries or dependency direction. Escalate to `reliability-observability-gate` when shutdown, startup validation, or pool ownership affects production readiness. Escalate to `security-privacy-gate` when global state or service locator access can bypass auth, tenant, or secret boundaries.

# Critical Details

- Composition root owns production graph construction; ordinary business code receives collaborators, not containers.
- Constructor injection is preferred for required stable collaborators.
- Factory injection is used when each operation needs a fresh domain object or short-lived resource.
- Provider injection is used when lazy access is justified and still typed/test-controlled.
- App-scoped dependencies include reusable HTTP, DB, Redis, Kafka, telemetry, and SDK clients.
- Module-scoped dependencies are shared inside a module but hidden behind its facade.
- Request, job, and transaction scopes carry identity, cancellation, transaction, unit-of-work, and per-operation state.
- Singleton lifecycle is acceptable only with immutability or synchronized state, startup validation, reset strategy for tests, and shutdown cleanup.
- Lazy initialization must state race behavior, error caching, retry behavior, and first-use latency.
- Lifecycle leaks include timers, subscriptions, background loops, file handles, sockets, response bodies, clients, and pools.

# Failure Modes

- Creating a new HTTP, DB, Redis, Kafka, or SDK client inside every request or loop iteration.
- Hiding dependencies behind a service locator so tests and reviewers cannot see the graph.
- Adding a singleton with mutable state and no reset, synchronization, or shutdown path.
- Introducing circular service dependencies resolved by lazy lookup instead of fixing ownership.
- Letting tests patch globals in ways production wiring cannot reproduce.
- Forgetting to close pools, timers, subscriptions, streams, or sockets on shutdown.
- Binding untyped config late and discovering invalid wiring only after traffic starts.

# Output Contract

Return a Dependency Wiring Plan:

- Composition root.
- Dependency graph.
- Lifecycle scope per dependency.
- Construction owner.
- Shutdown owner.
- Startup validation.
- Test override strategy.
- Circular dependency check.
- Service locator rejection or justification.
- Client and pool lifecycle.
- Lazy versus eager initialization decision.
- Configuration binding.
- Residual lifecycle risk.

# Evidence Contract

Close the plan only when it identifies all new or changed dependencies, where each is constructed, its lifecycle scope, cleanup path, config binding, graph/cycle evidence, test override mechanism, validation command or review artifact, what the evidence proves and does not prove, and remaining lifecycle risks.

# Quality Gate

1. Every dependency has owner and lifecycle.
2. No reusable external client or pool is constructed per operation.
3. No hidden service locator is introduced without framework justification and test control.
4. No circular dependency exists, or the explicit exception is bounded and reviewed.
5. Shutdown path exists for every long-lived resource.
6. Test override is explicit and preserves production semantics.
7. Config binding is typed and validated at startup.
8. Lazy initialization is race-safe and observable.

# Used By

- backend-change-builder
- integration-change-builder
- data-middleware-change-builder
- reliability-observability-gate
- architecture-impact-reviewer
- ai-code-review-refactor
- quality-test-gate

# Handoff

Hand off to `implementation-structure-design` for placement, `language-performance-safety` for resource cleanup and pool performance, `configuration-runtime-policy` for config-driven graph variation, `architecture-impact-reviewer` for cross-module dependency direction, and `testability-seam-design` for test overrides.

# Completion Criteria

The capability is complete when the dependency graph is explicit, scoped, acyclic, reusable clients are long-lived at the correct owner, startup validation and shutdown cleanup exist, tests can override seams without changing production semantics, and residual lifecycle risk is named.
