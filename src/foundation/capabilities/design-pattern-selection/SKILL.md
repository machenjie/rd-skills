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

# Non-Negotiable Rules

- Pattern follows problem, not aesthetics; prefer boring direct code when variation is not current.
- Every pattern decision names the force it solves and the simpler alternative rejected.
- Every selected pattern declares object relationships, method placement, module/file impact, public API impact, lifecycle/ownership, side-effect visibility, invariant protection, and tests.
- Every selected pattern declares performance, concurrency, IO, resource, cancellation, backpressure, and teardown impact, then routes to `language-performance-safety`, `concurrency-control`, `profiling`, `async-job-design`, `idempotency-retry-design`, `cache-design`, or `reliability-observability-gate` when those concerns are present.
- Patterns must not bypass domain invariants, hide side effects, expand public API without current consumers, or create global mutable state without explicit lifecycle, synchronization, test reset, and shutdown cleanup.

# Industry Benchmarks

Anchor against Gang of Four pattern intent, Fowler refactoring and enterprise patterns, POSA concurrency and architecture patterns, domain-driven design aggregate and repository boundaries, Clean Architecture port/adapter dependency direction, SOLID with LSP and interface segregation, Little's Law for pool/queue sizing, Google SRE overload/backpressure guidance, and language runtime guidance for async blocking, lock scope, allocation, GC, and resource cleanup.

# Selection Rules

Start with direct code. Escalate only when a current force makes direct code worse than the pattern cost. Use `implementation-structure-design` first when object, method, module, split, or merge placement is part of the decision. Use `language-performance-safety` for hot path, allocation, GC, async, blocking/non-blocking IO, client/pool lifecycle, fan-out, backpressure, cancellation, or resource cleanup. Use `concurrency-control` for locks, races, deadlocks, shared mutable state, worker concurrency, and lock scope. Use `profiling` for object pool, allocation, contention, latency, or performance claims.

# Risk Escalation Rules

Escalate to `architecture-impact-reviewer` when the pattern changes module boundaries, dependency direction, public API, inheritance hierarchy, port/adapter boundary, or cross-service contract. Escalate to `quality-test-gate` when contract tests, public behavior tests, stress tests, or lifecycle cleanup tests are missing. Escalate to `reliability-observability-gate` when observer fan-out, worker pools, backpressure, circuit breaker, bulkhead, hidden IO, or production latency/SLO risk is present. Escalate to `integration-change-builder` when adapter, proxy, repository, or anti-corruption layer hides network/storage IO.

# Reference Loading Policy

Current mode is inline-only: this capability has no deep reference files today, so this `SKILL.md` contains the active decision rules. When deep references are added later, load them only when multiple pattern candidates, public interfaces/base classes/registries/providers, lifecycle/concurrency/IO/runtime risk, L3+ scope, or AI-generated pattern usage without evidence is present.

Do not load deep references for direct-code decisions with one local rule, one owner, no selected pattern, and no public API, lifecycle, concurrency, IO, or runtime risk.

# Critical Details

## Pattern Matrix

| Pattern | Use when | Reject when | Object relationship | Performance risk | Test boundary |
| --- | --- | --- | --- | --- | --- |
| Factory Method | one product family has current variants or construction policy | simple constructor is enough | creator owns construction policy | per-call heavy construction | constructor contract and variant creation |
| Abstract Factory | families of related objects must vary together | one family or speculative provider | factory family plus products | object graph churn | family compatibility contract |
| Builder | construction has many validated steps or immutable aggregate setup | trivial DTO | builder owns construction state | allocation and validation cost | invalid/complete build behavior |
| Prototype | cloning configured objects is cheaper or preserves setup | copy semantics unclear | source prototype to clone | stale mutable state | deep/shallow copy contract |
| Singleton | one lifecycle-owned process resource is required | hidden global mutable state | global owner plus consumers | lock contention, test reset | lifecycle, sync, teardown tests |
| Object Pool | measured allocation/connection cost dominates | no profile evidence | pool owns reusable objects | contention, stale reset | profile, reset, leak tests |
| Adapter | external protocol or legacy shape differs from domain contract | same contract or only naming | port plus adapter | hidden IO or mapping cost | contract plus resource cleanup |
| Facade | simplify a stable subsystem API | god object or policy dumping ground | facade to cohesive subsystem | latency aggregation | public facade behavior |
| Decorator | add ordered cross-cutting behavior to same contract | side effects/order hidden | wrapper chain | allocation, latency, order | contract and ordering tests |
| Proxy | control remote/lazy/access behavior through same contract | network IO hidden | proxy to subject | hidden latency, timeout | IO timeout and cleanup tests |
| Composite | tree of uniform parts and whole operations exists | no real tree | parent/child tree | traversal cost | tree invariants and traversal |
| Bridge | abstraction and implementation axes vary independently | one axis only | abstraction delegates to implementor | dispatch and allocation | each axis contract |
| Strategy | multiple current algorithms behind stable interface | one implementation | context plus strategy family | dispatch/allocation overhead | shared contract tests |
| State | object has real state machine with state-specific behavior | flags are simple | context plus state objects | object churn | transition/invalid path tests |
| Command | actions need queue, undo, audit, retry, or scheduling | direct call is enough | command plus handler | allocation, idempotency/retry | command contract and retry tests |
| Observer/PubSub | event fan-out has independent subscribers | no unsubscribe/lifecycle | publisher to subscribers | unbounded fan-out | unsubscribe, backpressure, isolation |
| Mediator | peer objects need coordinated interaction | mediator becomes god object | peers through mediator | bottleneck | interaction contract |
| Chain of Responsibility | ordered handlers may accept/pass work | fixed if/else clearer | linked handlers | hidden order, latency | order and fallback tests |
| Template Method | stable algorithm skeleton with variant hooks | base class only for reuse | base skeleton plus subclass hooks | inheritance cost | base/subclass contract |
| Visitor | many operations traverse stable object structure | breaks encapsulation | visitor to elements | traversal and coupling | operation/element matrix |
| Specification | reusable predicates combine domain policies | one local predicate | policy object/value | allocation and query translation | predicate and composition tests |
| Null Object | default no-op preserves contract safely | hides missing data/error | concrete no-op implementation | silent behavior | explicit no-op contract |
| Repository | domain needs persistence boundary | business policy in repository | domain/service to repository | storage IO hidden | persistence contract and transactions |
| Unit of Work | changes must commit atomically across repositories | one simple write | UoW owns transaction | long transactions/locks | commit/rollback tests |
| Dependency Injection | dependencies vary by environment/test/runtime | service locator hides deps | constructor/config ownership | lifecycle churn | wiring and contract tests |
| Domain Event | committed domain change fans out asynchronously | event before invariant commit | aggregate emits event | duplicate/fan-out cost | outbox/idempotency tests |
| Port/Adapter | domain must not depend on external protocol | adapter leaks domain policy | port contract plus adapter | IO lifecycle | provider contract tests |
| Anti-Corruption Layer | external model conflicts with domain language | simple mapping is enough | translation boundary | mapping/latency cost | translation contract |
| Producer-Consumer | producer and consumer rates differ | synchronous flow is enough | queue boundary | queue growth | bounded queue tests |
| Worker Pool | bounded parallel workers process work | unbounded tasks or no load | pool owns workers | saturation | pool, cancellation tests |
| Pipeline | staged transforms have independent rates | stages are trivial | stage chain | buffering/backpressure | stage and end-to-end tests |
| Reactor/Proactor | IO multiplexing or async completion is central | blocking thread model is simpler | event loop plus handlers | event-loop blocking | non-blocking tests |
| Bounded Fan-out | async tasks fan out today | unbounded gather/all | coordinator plus semaphore | queue/task growth | timeout/cancellation tests |
| Backpressure | downstream cannot accept unlimited work | caller can fail fast simply | producer to bounded consumer | latency and drops | overload behavior tests |
| Circuit Breaker/Bulkhead | dependency failure isolation is needed | local direct call only | boundary guard | state/metric cost | reliability gate contract |

## Pattern Anti-Patterns

Reject strategy with one implementation; abstract base class only for code reuse; singleton as hidden mutable state; factory hiding a simple constructor; builder for a trivial DTO; observer without unsubscribe, lifecycle cleanup, backpressure, and error isolation; decorator hiding side effects or order dependency; proxy hiding network IO; facade or mediator becoming a god object; visitor breaking encapsulation; object pool without measured allocation pressure; command without idempotency/retry model; state pattern without a real state machine; repository carrying business policy; and DI container service locator hiding dependencies.

## Runtime Coupling

Pattern selection is a structure decision and a runtime decision. Factory, builder, strategy, decorator, proxy, repository, worker, observer, and pipeline choices can introduce allocation, dispatch, hidden IO, client construction, stream cleanup, queue growth, lock scope, task lifetime, or cancellation obligations. Record those obligations before accepting the pattern.

# Failure Modes

- Pattern overengineering: strategy, factory, interface, registry, or abstract base for one implementation.
- Side-effect opacity: proxy, decorator, repository, observer, or facade hides network/storage IO, retries, events, or mutation.
- Lifecycle leak: singleton, observer, worker pool, task fan-out, subscription, stream, file descriptor, or client/pool is not shut down.
- Invariant bypass: repository, command, visitor, or adapter moves policy away from the domain owner.
- Runtime regression: pattern adds hot-path allocation, lock contention, event-loop blocking, unbounded fan-out, missing backpressure, or per-operation client construction.

# Output Contract

Return a Design Pattern Decision Record:

- problem/force
- pattern candidates
- selected pattern or direct-code decision
- rejected patterns and reasons
- simpler alternative considered
- object relationship map
- method placement impact
- module/file placement impact
- public API impact
- lifecycle/ownership impact
- performance/concurrency/IO risk
- side-effect visibility
- invariant protection
- tests/contract tests
- deletion/reversal path
- residual risk

# Quality Gate

1. No pattern without current force and rejected simpler alternative.
2. No speculative abstraction, public API, registry, interface, inheritance, factory, or provider without current consumers or variants.
3. Object relationships, method ownership, module/file placement, lifecycle, and side effects are explicit.
4. Performance, concurrency, IO, cancellation, backpressure, cleanup, and pool/client lifecycle are explicit and routed to adjacent capabilities when present.
5. Object Pool has profile evidence; Singleton/global state has lifecycle, thread-safety, test reset, and shutdown cleanup.
6. Observer/PubSub has unsubscribe, backpressure, bounded fan-out, and error isolation.
7. Proxy/Adapter/Repository declare IO, timeout, retry, resource cleanup, and visibility at the call site.
8. Command/Worker/Queue declare idempotency, retry, backpressure, cancellation, and partial failure.
9. Public behavior or contract tests prove the selected pattern and the rejected direct-code alternative remains cheaper to delete.

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
