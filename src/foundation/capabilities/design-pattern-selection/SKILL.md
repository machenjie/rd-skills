---
name: design-pattern-selection
description: Selects, rejects, and validates design patterns only when they solve a current force in object relationships, variation, lifecycle, concurrency, IO, test boundaries, extension points, or public contracts.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "106"
changeforge_version: 0.1.0
---

# Mission

Select, reject, and verify design patterns. A pattern must solve a real current force: construction complexity, algorithm variation, state transition, event fan-out, external protocol boundary, lifecycle management, API facade, command history, traversal, composition tree, object creation cost, concurrency boundary, IO boundary, test boundary, extension point, or public contract. Reject patterns added to look professional.

# When To Use

Use when creating or changing object relationships; multiple algorithms, states, commands, events, construction paths, or external protocols exist now; a change considers factory, builder, strategy, observer, decorator, proxy, facade, command, state, template, visitor, composite, bridge, singleton, object pool, worker pool, pipeline, or adapter; object placement, module organization, file split/merge, lifecycle, performance, IO, or concurrency may be affected; or AI-generated code adds interfaces, abstract classes, registries, factories, providers, managers, or pattern names without evidence.

# Do Not Use When

Do not use to justify speculative abstraction, one current implementation, simple if/else that is clearer, code reuse alone, file-length reduction, testing private helpers, or a pattern that hides side effects, global state, lifecycle, dependency direction, domain invariants, IO, lock scope, allocation, or runtime cost.

# Stage Fit

Use during planning when a proposed object relationship, abstraction, interface, factory, strategy, state object, observer, worker, pool, pipeline, or adapter changes ownership or variation. Use during coding and review when AI-generated or human code introduces pattern names, inheritance, registries, providers, managers, hidden IO, or lifecycle boundaries. Use during testing and release when public behavior, contract compatibility, runtime cost, cleanup, rollback, or graph-memory evidence decides whether the pattern is accepted.

# Non-Negotiable Rules

- Pattern follows problem, not aesthetics; prefer boring direct code when variation is not current.
- Every pattern decision names the force it solves and the simpler alternative rejected.
- Reject factory with one product, builder for a trivial DTO, strategy with one algorithm, abstract/interface layer for code sharing, singleton for convenience, facade/mediator as a generic dumping ground, and proxy/decorator that hides IO or side effects.
- Every selected pattern declares object relationships, method placement, module/file impact, public API impact, lifecycle/ownership, side-effect visibility, invariant protection, and tests.
- Every selected pattern declares performance, concurrency, IO, resource, cancellation, backpressure, and teardown impact, then routes to `language-performance-safety`, `concurrency-control`, `profiling`, `async-job-design`, `idempotency-retry-design`, `cache-design`, or `reliability-observability-gate` when those concerns are present.
- Patterns must not bypass domain invariants, hide side effects, expand public API without current consumers, or create global mutable state without explicit lifecycle, synchronization, test reset, and shutdown cleanup.
- Current evidence is mandatory: cite repository graph, existing same-pattern usage, current variants or absence, project memory with dates, runtime/IO/concurrency evidence, public consumers, tests, and validation freshness before selecting a pattern.

# Industry Benchmarks

Anchor against Gang of Four pattern intent, Fowler refactoring and enterprise patterns, POSA concurrency and architecture patterns, domain-driven design aggregate and repository boundaries, Clean Architecture port/adapter dependency direction, SOLID with LSP and interface segregation, Little's Law for pool/queue sizing, Google SRE overload/backpressure guidance, and language runtime guidance for async blocking, lock scope, allocation, GC, and resource cleanup.

# Selection Rules

Start with direct code. Escalate only when a current force makes direct code worse than the pattern cost. Use `implementation-structure-design` first when object, method, module, split, or merge placement is part of the decision. Use `language-performance-safety` for hot path, allocation, GC, async, blocking/non-blocking IO, client/pool lifecycle, fan-out, backpressure, cancellation, or resource cleanup. Use `concurrency-control` for locks, races, deadlocks, shared mutable state, worker concurrency, and lock scope. Use `profiling` for object pool, allocation, contention, latency, or performance claims.

# Mode Matrix

| Mode | Trigger signals | Decision focus | Required evidence | Companion capabilities | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| Direct-code rejection | One implementation, simple branch, local construction, or pattern name with no current variants. | Prove the pattern is unnecessary and keep behavior visible. | Current force absent, same-pattern scan, direct-code alternative, deletion path, tests or not-verified limit. | `minimal-correct-implementation`, `code-clarity-maintainability` | Skip deep pattern matrix when no public API, lifecycle, IO, or concurrency risk exists. |
| Pattern acceptance | Current variants, protocol translation, state machine, fan-out, queue, lifecycle owner, or public contract exists now. | Select one pattern and reject cheaper patterns with object and module ownership. | Variant/consumer inventory, object relationship map, method placement, public contract impact, validation command. | `implementation-structure-design`, `quality-test-gate` | Skip future-proof abstractions and one-implementation interfaces. |
| Runtime/lifecycle pattern | Factory, singleton, proxy, observer, pool, worker, pipeline, decorator, or repository changes allocation, IO, locks, cleanup, or backpressure. | Keep runtime costs and side effects visible at the owning boundary. | Lifecycle owner, timeout/retry/cancellation rule, cleanup path, profile/stress/load validator or residual risk. | `language-performance-safety`, `concurrency-control`, `reliability-observability-gate` | Skip runtime redesign when direct code keeps lifecycle simpler. |
| Contract/testability seam | Pattern changes public API, generated client, inheritance hierarchy, extension point, or test seam. | Preserve consumer compatibility and public-behavior testing. | API/boundary diff, consumer inventory, contract/public-behavior test output, migration or rollback path. | `consumer-impact-analysis`, `contract-testing`, `testability-seam-design` | Skip private-helper exports and mock-internal patterns. |

# Proactive Professional Triggers

- **Signal:** a diff adds an interface, abstract class, base class, factory, builder, strategy, provider, registry, manager, singleton, facade, adapter, decorator, observer, worker pool, object pool, or pattern name. **Hidden risk:** speculative abstraction creates public API, hidden lifecycle, and harder deletion without solving a current force. **Required professional action:** require current variants, rejected direct-code alternative, ownership, deletion path, and tests before accepting the pattern. **Route to:** `design-pattern-selection`, `minimal-correct-implementation`, `implementation-structure-design`, and `quality-test-gate`. **Evidence required:** graph paths, current variants or collapse decision, simpler alternative, public behavior tests, and deletion path.
- **Signal:** project memory, prior pattern usage, framework convention, generated code, or AI rationale recommends a pattern. **Hidden risk:** stale or copied pattern memory can import another module's forces, side effects, or lifecycle assumptions into the wrong boundary. **Required professional action:** treat memory as a hypothesis, compare with current repository graph, local naming/placement conventions, and execution evidence. **Route to:** `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis`, and this capability. **Evidence required:** source/date, local same-pattern scan, accepted/rejected assumptions, and stale evidence limit.
- **Signal:** pattern hides network, database, cache, filesystem, queue, clock, randomness, process, thread, task, stream, subscription, or external API behavior behind a simple method call. **Hidden risk:** side-effect opacity causes timeout, retry, cleanup, cancellation, backpressure, lock, or observability gaps. **Required professional action:** expose side-effect boundary and route runtime/reliability capabilities before approval. **Route to:** `language-performance-safety`, `concurrency-control`, `reliability-observability-gate`, and `integration-change-builder` when external IO is present. **Evidence required:** side-effect map, lifecycle/cleanup owner, timeout/cancellation/backpressure rule, and validation command.
- **Signal:** pattern changes public API, inheritance hierarchy, module boundary, dependency direction, generated client, SDK contract, or framework extension point. **Hidden risk:** local structure choice becomes downstream compatibility or architecture drift. **Required professional action:** require contract impact, substitutability, dependency-direction check, and migration/reversal plan. **Route to:** `architecture-impact-reviewer`, `contract-testing`, `consumer-impact-analysis`, and this capability. **Evidence required:** API/boundary diff, consumer inventory, compatibility tests, and rollback/deletion path.
- **Signal:** pattern is introduced to make tests easier by exporting private helpers, mocking internals, or injecting a test-only abstraction. **Hidden risk:** tests freeze implementation details and miss public behavior. **Required professional action:** select public-behavior seam or reject the pattern. **Route to:** `testability-seam-design`, `quality-test-gate`, `code-clarity-maintainability`, and this capability. **Evidence required:** public behavior boundary, rejected private-helper access, seam map, and assertion that fails if the behavior branch is removed.
- **Signal:** repository graph, project memory, prior execution trace, benchmark, or earlier validation is used to approve a pattern after the object graph, public contract, runtime path, or final diff has changed. **Hidden risk:** stale graph or memory accepts the wrong pattern and closes with unverified validation. **Required professional action:** verify current source graph, compare memory as hypothesis only, rerun stale execution evidence, and record the handoff owner for remaining risk. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, `validation-broker`, and this capability. **Evidence required:** graph scan command or report, memory source/date, execution log path, validator exit code, stale evidence limit, and rollback note.

# Risk Escalation Rules

Escalate to `architecture-impact-reviewer` when the pattern changes module boundaries, dependency direction, public API, inheritance hierarchy, port/adapter boundary, or cross-service contract. Escalate to `quality-test-gate` when contract tests, public behavior tests, stress tests, or lifecycle cleanup tests are missing. Escalate to `reliability-observability-gate` when observer fan-out, worker pools, backpressure, circuit breaker, bulkhead, hidden IO, or production latency/SLO risk is present. Escalate to `integration-change-builder` when adapter, proxy, repository, or anti-corruption layer hides network/storage IO.

# Reference Loading Policy

Default mode is inline-only: this `SKILL.md` contains the active decision rules and output contract. Load deep references only when the inline rules cannot safely close the decision:

- [references/pattern-matrix.md](references/pattern-matrix.md): L3+ work, multiple pattern candidates, public interfaces/base classes/registries/providers, lifecycle/concurrency/IO/runtime risk, or AI-generated pattern usage without evidence.
- [references/pattern-evidence-record.md](references/pattern-evidence-record.md): decisions that rely on repository graph, project memory, execution traces, prior validation, same-pattern scans, or stale evidence reconciliation.
- [references/runtime-contract-coupling.md](references/runtime-contract-coupling.md): patterns that touch public contracts, generated clients, adapters, IO, concurrency, queues, pools, cancellation, backpressure, teardown, or production reliability.

Do not load deep references for L1/L2 direct-code decisions where the inline output contract can name one local rule, one owner, no selected pattern, and no public API, lifecycle, concurrency, IO, or runtime risk.

# Critical Details

## Pattern Selection Shortcuts

- Construction patterns need current variants, validated setup, lifecycle ownership, or measured allocation cost; otherwise prefer constructors and direct composition.
- Structural patterns need a real protocol, subsystem, tree, abstraction axis, or translation boundary; otherwise they hide coupling behind names.
- Behavioral patterns need current algorithm variation, state-machine behavior, command history, fan-out, traversal, or policy composition; otherwise direct code is cheaper.
- Runtime patterns need measured contention, IO multiplexing, bounded concurrency, overload control, or dependency isolation; otherwise they add invisible lifecycle and cleanup obligations.
- Load `references/pattern-matrix.md` when a detailed pattern-by-pattern use/reject/test comparison is needed.
- Load `references/pattern-evidence-record.md` when graph, memory, or execution evidence could be stale or contradictory.
- Load `references/runtime-contract-coupling.md` when a selected pattern could alter contracts, IO visibility, concurrency, queues, pools, cancellation, teardown, or reliability behavior.

## Pattern Anti-Patterns

Reject strategy with one implementation; abstract base class or interface only for code reuse; singleton as hidden mutable state or convenience; factory hiding a simple constructor or one product; builder for a trivial DTO; observer without unsubscribe, lifecycle cleanup, backpressure, and error isolation; decorator hiding side effects or order dependency; proxy hiding network IO; facade or mediator becoming a god object; visitor breaking encapsulation; object pool without measured allocation pressure; command without idempotency/retry model; state pattern without a real state machine; repository carrying business policy; and DI container service locator hiding dependencies.

## Runtime Coupling

Pattern selection is a structure decision and a runtime decision. Factory, builder, strategy, decorator, proxy, repository, worker, observer, and pipeline choices can introduce allocation, dispatch, hidden IO, client construction, stream cleanup, queue growth, lock scope, task lifetime, or cancellation obligations. Record those obligations before accepting the pattern.

# Failure Modes

- **Speculative abstraction:** strategy, factory, interface, registry, provider, or abstract base is accepted for one implementation and becomes hard to delete.
- **Wrong current force:** a pattern solves copied memory, framework fashion, or AI rationale instead of a current repository variant, lifecycle, contract, or runtime pressure.
- **Side-effect opacity:** proxy, decorator, repository, observer, facade, or adapter hides network/storage IO, retries, events, mutation, or partial failure from the call site.
- **Lifecycle leak:** singleton, observer, worker pool, task fan-out, subscription, stream, file descriptor, response body, or client/pool lacks teardown on success, error, timeout, cancellation, or shutdown.
- **Invariant bypass:** repository, command, visitor, adapter, or service moves domain policy away from the owner that protects state, permissions, transaction boundaries, or business rules.
- **Runtime regression:** pattern adds hot-path allocation, lock contention, event-loop blocking, unbounded queue/fan-out, missing backpressure, or per-operation client construction.
- **Contract drift:** public API, SDK, generated client, extension point, or inheritance hierarchy changes without consumer inventory, compatibility test, migration path, or rollback note.
- **Test seam distortion:** private helpers are exported, internals are mocked, or a test-only abstraction is added while public behavior remains unverified.
- **Stale evidence closure:** repository graph, project memory, benchmark, validator report, or same-pattern scan predates the final structure edit and is still used as completion evidence.

# Output Contract

Return a Design Pattern Decision Record:

- `mode_selected` (direct-code rejection, construction, structural, behavioral, runtime/concurrency, adapter/integration, public-contract, or testability-seam decision)
- `boundaries_inspected` (same file/module, sibling modules, existing patterns, public APIs, tests, runtime/IO/concurrency surfaces, project memory, and skipped boundaries with reason)
- `source_evidence` (current files, repository graph, same-pattern scan, current variants/consumers, benchmark/profile traces, tests, and memory date)
- `problem_force` (current force; why direct code is insufficient or why direct code is selected)
- `pattern_candidates` (selected pattern or direct-code decision, rejected patterns, rejected simpler alternative, and deletion/reversal path)
- `object_relationship_map` (roles, ownership, collaborator direction, inheritance/composition, method placement, module/file placement, and dependency direction)
- `public_contract_impact` (public API, SDK/client, generated code, extension point, serialization, and compatibility impact)
- `lifecycle_runtime_impact` (ownership, setup/teardown, side-effect visibility, IO, timeout, retry, cancellation, backpressure, concurrency, allocation, profiling need, and cleanup)
- `invariant_protection` (domain/business invariants preserved, bypass risks, and owner boundary)
- `pattern_to_validation_map` (public behavior, contract, stress, lifecycle cleanup, concurrency, performance, and regression evidence per selected or rejected pattern)
- `graph_memory_execution_validation` (accepted/rejected memory, same-pattern scan, execution/profiling evidence, stale validation, and not-verified disclosures)
- `validation_evidence` (command or test/validator, working directory, exit code, relevant output, report or artifact path, freshness after final edit, and what the evidence proves or does not prove)
- `residual_risk` and `evidence_limits` (what evidence proves, what it does not prove, remaining owner, and next gate)

# Quality Gate

1. No pattern without current force and rejected simpler alternative.
2. No speculative abstraction, public API, registry, interface, inheritance, factory, or provider without current consumers or variants.
3. Boundaries inspected, source evidence, graph-memory-execution validation, and evidence limits are recorded.
4. Object relationships, method ownership, module/file placement, lifecycle, side effects, dependency direction, and public contract impact are explicit.
5. Performance, concurrency, IO, cancellation, backpressure, cleanup, and pool/client lifecycle are explicit and routed to adjacent capabilities when present.
6. Object Pool has profile evidence; Singleton/global state has lifecycle, thread-safety, test reset, and shutdown cleanup.
7. Observer/PubSub has unsubscribe, backpressure, bounded fan-out, and error isolation.
8. Proxy/Adapter/Repository declare IO, timeout, retry, resource cleanup, and visibility at the call site.
9. Command/Worker/Queue declare idempotency, retry, backpressure, cancellation, and partial failure.
10. Public behavior or contract tests prove the selected pattern, and validation is fresh after the final structure edit.
11. Same-pattern scan records sibling occurrences and why they were reused, updated, or skipped.
12. Direct-code remains the accepted outcome when current-force, variant, lifecycle, or validation evidence is missing.
13. Validation command, test or validator name, output, exit code, report or artifact path, and stale/not-run evidence are recorded before handoff.

# Evidence Contract

Close a pattern decision only when the answer cites current source boundaries, boundaries inspected and skipped, same-pattern scan, current force, rejected direct-code alternative, object relationship map, lifecycle/runtime/side-effect impact, validation evidence from a command, test, validator, output, exit code, report, or artifact, what evidence proves, what evidence does not prove, residual risk, handoff owner, and next gate. Project memory, pattern names, or framework convention alone are not evidence.

# Benchmark Coverage

Pattern catalogs and architecture texts calibrate intent, but approval requires repository-local evidence: current variants, caller graph, object ownership, side-effect map, public consumers, lifecycle and runtime obligations, and tests at the observable behavior boundary.

# Routing Coverage

When selected by a router, report which adjacent capabilities were loaded or intentionally skipped: `minimal-correct-implementation`, `implementation-structure-design`, `code-clarity-maintainability`, `language-performance-safety`, `concurrency-control`, `profiling`, `async-job-design`, `idempotency-retry-design`, `cache-design`, `reliability-observability-gate`, `contract-testing`, `consumer-impact-analysis`, `testability-seam-design`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker`.

# Used By

- implementation-structure-design
- architecture-impact-reviewer
- backend-change-builder
- frontend-change-builder
- ai-code-review-refactor
- refactoring
- quality-test-gate

# Handoff

Hand off to `implementation-structure-design` for object-method-module placement, split/merge, inheritance/composition, and file granularity. Hand off to `language-performance-safety` for allocation, GC, async, blocking/non-blocking IO, hot path, resource cleanup, and client/pool lifecycle. Hand off to `concurrency-control` for locks, races, deadlocks, shared state, and worker coordination. Hand off to `profiling` when performance evidence is required. Hand off to `idempotency-retry-design` or `async-job-design` for command, queue, retry, fan-out, worker, and cancellation designs. Hand off to `reliability-observability-gate` for circuit breaker, bulkhead, backpressure, and production SLO risk.

# Completion Criteria

The capability is complete when the agent returns a Design Pattern Decision Record that either selects direct code or selects a pattern with named current force, rejected simpler alternatives, object relationship map, method placement, module/file placement, public API impact, lifecycle/ownership, runtime risk, invariant protection, side-effect visibility, tests, deletion path, and residual risk, with adjacent performance, concurrency, IO, reliability, profiling, idempotency, async-job, or cache capabilities selected only when their signals are present.
