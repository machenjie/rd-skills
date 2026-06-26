---
name: dependency-wiring-lifecycle
description: Governs dependency construction, injection, lifecycle scope, composition roots, reusable client ownership, startup validation, test overrides, and shutdown cleanup for services, jobs, adapters, and modules.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "108"
changeforge_version: 0.1.0
---

# Mission

Make dependency graphs explicit, acyclic, testable, observable, and resource-safe by deciding where dependencies are created, how they are injected, how long they live, who validates them at startup, who shuts them down, and how graph, memory, and execution evidence prove the wiring claim is current.

# When To Use

Use when adding or changing constructors, factories, providers, dependency injection containers, composition roots, service clients, DB pools, Redis/Kafka/HTTP/SDK clients, token refreshers, webhook verifiers, schedulers, timers, subscriptions, sockets, streams, file handles, background loops, worker pools, or test overrides.

Use when per-operation client construction, service locator access, global mutable state, circular dependency, lazy initialization, config-driven wiring, startup validation, test override semantics, shutdown cleanup, graph freshness, or lifecycle ownership is unclear.

# Do Not Use When

Do not use for pure functions or data-only DTO changes with no collaborators or resources.

Do not use to introduce a dependency injection framework where direct construction in the existing composition root is simpler and local convention supports it.

# Stage Fit

Use during implementation planning before new collaborators or resources are introduced, during code review when a diff adds clients, pools, providers, service locators, globals, background loops, or test seams, during reliability/release review when startup and shutdown behavior matters, and during repair when leaks, circular graphs, hidden dependencies, stale project-memory claims, or flaky tests trace back to wiring. Re-enter after config, generated clients, module boundaries, graph evidence, validation commands, or test overrides change.

# Non-Negotiable Rules

- **Every dependency has a construction owner and lifecycle scope.** Composition root, module facade, request/job/transaction scope, factory, provider, adapter, or test harness ownership must be named.
- **Reusable clients and pools are not constructed per operation.** HTTP, DB, Redis, Kafka, SDK, telemetry, worker, token, and webhook clients are long-lived at the narrowest safe owner unless measured evidence proves otherwise.
- **Business code receives collaborators, not containers.** Service locator and container access inside domain, service, mapper, policy, or job logic is rejected unless framework convention requires it and tests can control it without changing production semantics.
- **Global mutable state needs ownership, synchronization, reset, observability, and shutdown.** A singleton without those answers is unowned state, not lifecycle design.
- **Long-lived resources need startup validation and cleanup.** Pools, timers, subscriptions, streams, sockets, cursors, file handles, background loops, and workers must have acquisition, health validation, cancellation, and close paths.
- **Dependency graph claims require current graph evidence.** A local read or memory note is not proof that the graph is acyclic, current, or testable; graph scope, omitted edges, and freshness limits must be recorded.
- **Test overrides preserve production semantics.** Tests can replace external boundaries through declared seams, but must not patch globals, bypass config validation, or build a graph impossible in production.
- **Config-driven wiring is typed and bounded.** Provider, mode, region, tenant, experiment, or flag choices must be validated before graph construction and must not become hidden strategy registries.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Composition-root wiring | Constructor, module factory, DI container, provider graph, or app setup changes. | Source-of-truth owner, graph shape, dependency direction, acyclic construction. | Composition root path, dependency graph, owner, cycle check, rejected locations. | `implementation-structure-design`, `module-boundary-design` | Creating new container/framework. |
| Reusable client or pool lifecycle | HTTP/DB/Redis/Kafka/SDK/telemetry client, pool, token refresher, verifier, worker, or connection changes. | Correct scope, reuse, health check, pool config, close path. | Lifecycle scope, construction/shutdown owner, startup validation, metrics. | `language-performance-safety`, `reliability-observability-gate` | Per-operation construction. |
| Request/job/transaction scope | Identity, cancellation, unit-of-work, transaction, job context, or per-operation state changes. | Avoid leaking per-operation state into globals or app scope. | Scope boundary, propagation path, cleanup, concurrency semantics. | `transaction-consistency`, `concurrency-control` | Global mutable context. |
| Lazy/provider/service locator | Lazy init, provider injection, service locator, optional dependency, or plugin registry appears. | Race behavior, error caching, test control, framework justification. | Lazy/eager decision, concurrency behavior, retry, first-use latency, override plan. | `code-clarity-maintainability`, `testability-seam-design` | Hidden container lookup. |
| Config-driven wiring | Provider/mode/region/tenant/flag selects dependency graph or implementation. | Typed config, bounded variation, startup fail-fast, rollback. | Config schema, default, validation, graph variant matrix, owner. | `configuration-runtime-policy`, `secret-configuration-security` | Untyped mode switch. |
| Test override and seam | Tests need fake/stub/mock/spy, clock/random/env override, sandbox client, or fixture graph. | Preserve production graph semantics while making behavior deterministic. | Seam map, override owner, fixture owner, contract/integration proof. | `testability-seam-design`, `quality-test-gate` | Patching private globals. |
| Graph freshness repair | Existing graph, memory, or earlier validation claims wiring is safe. | Refresh, accept, reject, or downgrade stale evidence. | Source reread, graph slice, memory verdict, trajectory/validation freshness. | `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis` | Trusting old notes. |

# Industry Benchmarks

Anchor against composition root practice, constructor injection, dependency inversion, twelve-factor config binding, framework lifecycle hooks, connection pooling and graceful shutdown guidance, structured concurrency, resource leak detection, dependency graph checks, DI container module validation, and test double contract discipline. Keep the body focused on route-time decisions, output evidence, and lifecycle gates; add deep references only when concrete lifecycle matrices exceed the inline contract.

# Selection Rules

Select this capability when the primary risk is **dependency graph ownership, lifecycle scope, resource safety, or test override fidelity**. Prefer `implementation-structure-design` when file/function/object placement is the main decision; use both when placement changes construction ownership. Use `language-performance-safety` for clients, pools, timers, subscriptions, sockets, descriptors, event loops, cancellation, and cleanup. Use `configuration-runtime-policy` when config drives graph variation. Use `testability-seam-design` when override seams are unclear. Use `repository-graph-analysis`, `project-memory-governance`, and `execution-trajectory-analysis` when graph, memory, or validation freshness affects the wiring claim.

# Proactive Professional Triggers

- **Signal:** HTTP, DB, Redis, Kafka, SDK, telemetry, token, webhook, pool, or worker is constructed inside a request, loop, handler, mapper, getter, or retry path. **Hidden risk:** connection churn, socket exhaustion, token churn, pool starvation, and untestable lifecycle. **Required professional action:** move ownership to the narrowest correct composition root or scoped factory. **Route to:** `language-performance-safety`, `reliability-observability-gate`. **Evidence required:** construction site, intended scope, reuse proof, shutdown owner, pool/client metric.
- **Signal:** Business logic calls a container, registry, global singleton, service locator, or dynamic provider directly. **Hidden risk:** hidden graph edges, circular dependency, impossible test override, and auth/tenant/secret bypass. **Required professional action:** expose collaborator through constructor/factory/provider seam or justify framework convention. **Route to:** `implementation-structure-design`, `code-clarity-maintainability`, `security-privacy-gate` when boundaries are sensitive. **Evidence required:** owner boundary, rejected direct lookup, test-control path, dependency-direction check.
- **Signal:** A singleton or module global holds mutable state, cached credentials, tenant data, request state, timers, subscriptions, or background loops. **Hidden risk:** cross-request leakage, race, stale secret/config, flaky tests, and shutdown leaks. **Required professional action:** define synchronization, reset, refresh, observability, and cleanup. **Route to:** `concurrency-control`, `secret-configuration-security`, `testability-seam-design`. **Evidence required:** state owner, concurrency model, reset strategy, shutdown path.
- **Signal:** Lazy initialization is added to avoid cycle, startup cost, optional dependency, or config timing. **Hidden risk:** first-use latency, race on initialization, error caching ambiguity, and circular graph hidden until production. **Required professional action:** decide eager/lazy with race, retry, health, and observability rules. **Route to:** `failure-contract-design`, `reliability-observability-gate`. **Evidence required:** lazy/eager decision, failure behavior, cycle check, startup or first-use validation.
- **Signal:** Provider, mode, region, tenant, flag, experiment, or environment selects an implementation. **Hidden risk:** untyped config becomes hidden strategy system or invalid graph starts under traffic. **Required professional action:** type and validate config before graph construction and map graph variants. **Route to:** `configuration-runtime-policy`, `design-pattern-selection`. **Evidence required:** config schema/default, variant matrix, fail-fast behavior, rollout/rollback path.
- **Signal:** Tests patch globals, monkeypatch containers, replace private helpers, or build a graph production cannot build. **Hidden risk:** tests pass against a different system than production. **Required professional action:** design explicit override seam and contract/integration proof where needed. **Route to:** `testability-seam-design`, `quality-test-gate`. **Evidence required:** seam map, test double type, fixture owner, production-semantic preservation.
- **Signal:** Existing memory, report, graph, or prior validation says the dependency graph is safe. **Hidden risk:** later edits, generated outputs, config, or module moves made that claim stale. **Required professional action:** refresh graph or downgrade claim to selector-only before closure. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, `validation-broker`. **Evidence required:** graph freshness, accepted/rejected memory, validation order, changed-path map.

# Risk Escalation Rules

Escalate to `architecture-impact-reviewer` when wiring changes module boundaries, public facades, dependency direction, or creates cross-module cycles. Escalate to `reliability-observability-gate` when shutdown, startup validation, pool ownership, event loop blocking, background workers, or resource leaks affect production readiness. Escalate to `security-privacy-gate` when global state, service locator access, config, credentials, tenants, auth clients, or secrets can cross trust boundaries. Escalate to `quality-test-gate` when override seams, graph validation, or lifecycle cleanup lack executable evidence.

# Reference Loading Policy

Current mode is inline-only: this capability has no deep reference files today, so this `SKILL.md` owns the active dependency-graph and lifecycle rules.

If deep references are added later, load them only for L3+ work, cross-module composition roots, service locator risk, reusable client or pool lifecycle changes, shutdown cleanup gaps, or circular dependency evidence.

Do not load deep references for L1/L2 local collaborator changes where the inline output contract can name the construction owner, lifecycle scope, and cleanup decision.

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
- Dependency graph evidence includes current source reads, DI/container module definitions, provider registrations, factory call sites, imports, config variants, test harness overrides, generated clients, and build/install profile boundaries.
- Scope mismatch examples: app-scoped client carrying request identity, request-scoped transaction stored in singleton, tenant-specific provider cached globally, and test-only override bypassing startup validation.
- Shutdown cleanup should cover success, startup failure, cancellation, signal termination, test teardown, and rollback/redeploy paths where applicable.
- Startup validation should check required config, credentials reference shape without exposing secrets, provider reachability only when safe, pool/client configuration, and graph construction errors before accepting traffic.
- Graph, memory, and trajectory claims are closure inputs only after freshness is checked against final source, config, generated reports, validation, and build outputs.

# Failure Modes

- Creating a new HTTP, DB, Redis, Kafka, or SDK client inside every request or loop iteration.
- Hiding dependencies behind a service locator so tests and reviewers cannot see the graph.
- Adding a singleton with mutable state and no reset, synchronization, or shutdown path.
- Introducing circular service dependencies resolved by lazy lookup instead of fixing ownership.
- Letting tests patch globals in ways production wiring cannot reproduce.
- Forgetting to close pools, timers, subscriptions, streams, or sockets on shutdown.
- Binding untyped config late and discovering invalid wiring only after traffic starts.
- Caching tenant, credential, locale, transaction, or request context in an app-scoped singleton.
- Introducing lazy lookup to break a circular dependency instead of fixing ownership.
- Reusing stale graph or memory evidence after config, generated client, or module wiring changed.

# Output Contract

Return a `dependency_wiring_plan` with:

- `mode_selected` (composition-root wiring, reusable client/pool lifecycle, request/job/transaction scope, lazy/provider/service locator, config-driven wiring, test override and seam, or graph freshness repair).
- `source_evidence` (composition roots, constructors, factories, providers, DI/container modules, client/pool setup, config binding, shutdown hooks, tests/fixtures, generated artifacts, repository graph, project memory, execution trajectory, and skipped boundaries with reason).
- `graph_memory_trajectory_judgment` (accepted, rejected, stale, or not verified for prior graph, lifecycle ownership, test override, startup/shutdown validation, and previous validator claims).
- `dependency_inventory` (new/changed dependency, dependency type, resource handle, config inputs, identity/tenant/cancellation/transaction coupling, owner, and consumers).
- `dependency_graph` (nodes, edges, construction order, dependency direction, cycle check, module boundary impact, and omitted dynamic edges).
- `lifecycle_scope_matrix` (app, module, request, job, transaction, test, or short-lived scope per dependency; construction owner; shutdown owner; reset owner; observability owner).
- `construction_decision` (constructor/factory/provider/container/direct construction, rejected service locator/global/singleton path, and placement rationale).
- `resource_lifecycle` (startup validation, health check, cancellation, timeout, retry/refresh, close/drain/unsubscribe/stop path, and failure behavior).
- `configuration_binding` (typed config, default, validation timing, provider/mode variant matrix, secret boundary, rollout/rollback behavior).
- `test_override_strategy` (public behavior boundary, seam map, fake/stub/mock/spy decision, fixture owner, production-semantic preservation, contract/integration proof).
- `changed_dependency_to_validation_map` (each changed dependency, graph edge, scope, config variant, shutdown path, test override, generated artifact, and memory/graph claim mapped to validator, review, owner response, or residual risk).
- `handoff_boundaries` (what belongs to structure, config, performance, concurrency, security, reliability, testability, architecture, or release).
- `evidence_limits` and `residual_lifecycle_risk` (unknown dynamic edges, untested cleanup, missing telemetry, stale memory, partial graph, unsupported runtime profile, or unverified override with owner and next gate).

# Evidence Contract

Close the plan only when these answers are concrete:

- **Basis:** selected mode, changed dependency surface, lifecycle risk, and why wiring affects implementation, reliability, security, validation, or testability.
- **Current evidence:** source/config/test/generated/registry evidence inspected, graph slice, dynamic or omitted edges, project-memory signals, execution-order freshness, and skipped boundaries.
- **Wiring judgment:** dependency inventory, construction owner, lifecycle scope, dependency direction, cycle result, service-locator/global/singleton decision, config binding, startup validation, shutdown cleanup, and test override semantics.
- **Validation mapping:** every changed dependency, graph edge, lifecycle scope, config variant, startup/shutdown path, test override, generated artifact, memory claim, and cleanup criterion maps to executable proof, owner review, or named residual risk.
- **Evidence limits and handoff:** what source reads, graph evidence, memory, trajectory, tests, startup validation, leak checks, and manual review prove; what they do not prove; rollback note; residual risk owner; and next gate.

# Benchmark Coverage

This capability covers composition roots, dependency inversion, constructor/factory/provider/container decisions, reusable client and pool lifecycle, request/job/transaction scope, service locator rejection, singleton/global-state governance, lazy initialization, typed config-driven wiring, startup validation, graceful shutdown, test override seams, resource leak prevention, graph/memory/trajectory freshness, and changed-dependency-to-validation mapping without loading a broad repository context.

# Routing Coverage

Routes from `backend-change-builder`, `integration-change-builder`, `data-middleware-change-builder`, `reliability-observability-gate`, `architecture-impact-reviewer`, `ai-code-review-refactor`, and `quality-test-gate` should arrive here when lifecycle ownership, graph construction, reusable client/pool scope, service locator risk, global mutable state, lazy/provider semantics, config-driven wiring, shutdown cleanup, or test override fidelity is primary. Route away when the unresolved decision is file/object placement, runtime performance measurement, config policy, security review, test strategy, module boundary architecture, or release approval.

# Quality Gate

The dependency wiring plan is complete only when:

1. Selected mode, changed dependency surface, and source evidence are explicit.
2. Every new or changed dependency has construction owner, lifecycle scope, consumers, config inputs, and cleanup owner.
3. Reusable external clients, pools, token refreshers, verifiers, workers, timers, subscriptions, and handles are not constructed per operation.
4. Service locator, container lookup, global mutable state, and singleton usage are rejected or justified with framework convention, test control, synchronization/reset, and shutdown evidence.
5. Dependency graph is acyclic, or the exception is bounded, reviewed, observable, and has an exit plan.
6. Startup validation covers required config, graph construction, client/pool setup, safe credential reference checks, and failure behavior.
7. Shutdown cleanup covers pools, timers, subscriptions, streams, sockets, response bodies, background loops, workers, and test teardown where present.
8. Config-driven graph variation is typed, validated before use, bounded by variant matrix, and mapped to rollout/rollback.
9. Lazy initialization states race behavior, error caching, retry behavior, first-use latency, observability, and test override behavior.
10. Test overrides use explicit seams, preserve production wiring semantics, and avoid private/global patching unless justified and owned.
11. Graph freshness, project-memory reuse, execution trajectory, and validation freshness are recorded for any reused wiring claim.
12. Every changed dependency, graph edge, lifecycle scope, config variant, startup/shutdown path, and override seam maps to validator, review, owner response, or residual risk.
13. Handoff boundaries, evidence limits, rollback note, residual lifecycle risk, and next gate are explicit.

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
