---
name: testability-seam-design
description: Designs observable behavior test boundaries and explicit test seams without exporting private helpers or over-mocking internals; use when code needs deterministic tests across collaborators, time, randomness, concurrency, or external IO.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "107"
changeforge_version: 0.1.0
---

# Mission

Design code and tests so observable public behavior can be verified directly, while external systems, nondeterministic inputs, collaborators, fixtures, and schedules are controlled through explicit seams that preserve encapsulation, production semantics, and validation confidence. A test seam is successful only when it lets tests fail for the real risk without exporting private helpers, over-mocking internals, or hiding graph, memory, execution, or validation drift.

# When To Use

- When tests require fakes, stubs, mocks, spies, fixtures, generated data, deterministic clocks, random values, UUIDs, concurrency scheduling, environment variables, files, HTTP, databases, queues, caches, SDK clients, feature flags, or dependency graph overrides.
- When tests pressure implementation to export private helpers, widen visibility, split files, add interfaces, patch globals, monkeypatch containers, or assert internal call order.
- Before risky refactors when characterization tests must lock current observable behavior before moving code.
- When project memory, repository graph, test failures, flaky runs, or validation evidence suggests seams are stale, over-mocked, nondeterministic, or disconnected from real contracts.
- When a fake, mock, fixture, or test data builder represents an external contract, generated schema, integration boundary, public API, or side-effectful dependency.

# Do Not Use When

Do not use to justify testing private helpers directly, exporting internals, adding package-visible hooks, or inventing interfaces that have no production boundary and no explicit test seam.

Do not use when the change is a no-behavior edit and existing tests already prove the public contract.

Do not use to replace test-level strategy; route broad test depth decisions to `quality-test-gate` and use this capability for seam design.

# Stage Fit

Use during implementation planning, TDD design, refactoring, review, repair, validation, and final handoff when testability depends on public behavior boundaries, deterministic inputs, collaborator seams, fixture ownership, or test double fidelity. Re-enter after graph refresh, memory signal, helper export pressure, fixture reuse, flake repair, mock contract change, or validation rerun that can make seam evidence stale.

# Non-Negotiable Rules

- **Public behavior first:** test through API endpoint, service method, component behavior, CLI command, job outcome, repository contract, event contract, module facade, or other observable boundary before reaching into internals.
- **No test-only visibility widening:** do not make private code public, exported, package-visible, injectable, or split solely to make a smaller test possible.
- **Seams need a real boundary:** every new seam has production purpose, external boundary, nondeterministic source, lifecycle owner, or explicit test boundary; speculative interfaces are rejected.
- **Mock only declared boundaries:** mocks verify external interactions or explicitly declared seam behavior, not private call order or internal choreography.
- **Double fidelity is proven:** fakes, stubs, mocks, and spies representing real providers have contract, integration, fixture, or calibration evidence proportional to risk.
- **Determinism is designed:** time, randomness, UUIDs, concurrency, environment, process state, feature flags, file IO, network IO, DB/cache/queue state, and schedulers are controllable in tests.
- **Fixtures have owners:** fixture factories, builders, seeds, snapshots, and golden files belong to a module, contract, or domain test boundary and name their reason to change.
- **Characterization before movement:** risky refactors capture current observable behavior before extraction, split, merge, or dependency inversion.
- **Minimal evidence is risk-bound:** choose the cheapest test layer that can fail for the real risk, but do not under-test trust-boundary, contract, data, concurrency, security, accessibility, or release behavior.
- **Graph and validation coupling:** seam decisions map to dependency graph edges, affected tests, validation commands, and evidence limits before closure.

# Industry Benchmarks

Anchor against xUnit public behavior testing, ports-and-adapters seam design, London versus classical test double tradeoffs, consumer-driven contract testing, Testcontainers and controlled integration seams, Michael Feathers characterization tests, property-based testing for invariant-heavy logic, mutation testing for critical calculations, deterministic fake clocks/random/ID providers, and Testing Library guidance that tests should resemble user-visible behavior rather than implementation details.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Exit risk |
| --- | --- | --- | --- | --- | --- |
| Public behavior boundary | Tests reach private helpers, local mappers, hooks, component internals, or implementation call order. | Move proof to public behavior or record why no boundary exists. | Boundary under test, private-helper non-export decision, behavior assertion. | `implementation-structure-design`, `code-clarity-maintainability` | Tests freeze implementation, not behavior. |
| External dependency seam | HTTP, DB, queue, cache, file, SDK, provider, repository, event bus, or sandbox dependency. | Choose fake/stub/mock/spy/integration and prove fidelity. | Real contract source, double type, contract/integration check, failure behavior. | `contract-testing`, `integration-testing` | Mock validates impossible provider behavior. |
| Nondeterministic input seam | Clock, random, UUID, locale, timezone, scheduler, process/env state, feature flag. | Make input injectable, seeded, frozen, or centrally read. | Source boundary, default, test override, seed/timezone, replay implication. | `test-data-management`, `configuration-runtime-policy` | Flaky or non-reproducible test signal. |
| Dependency graph override | DI container, provider, service locator, singleton, factory, plugin registry, test graph. | Preserve production graph semantics while allowing deterministic override. | Seam map, override owner, graph variant, reset/cleanup path, validation. | `dependency-wiring-lifecycle`, `repository-graph-analysis` | Tests run a graph production cannot build. |
| Fixture and builder seam | Shared factory, fixture, seed, golden file, generated test data, snapshot. | Assign ownership and mutation policy. | Owner module, fields used by assertions, update/delete path, privacy/determinism. | `test-data-management`, `quality-test-gate` | Shared business fixture creates broad churn. |
| Characterization refactor seam | Risky refactor, legacy code, behavior movement, split/merge/extract. | Lock current behavior before structure changes. | Characterized public behavior, preserved bugs if needed, validation command. | `refactoring`, `regression-testing` | Refactor changes behavior silently. |
| Validation freshness seam | Prior test pass, stale report, changed fixture/mock/generated input, flaky repair. | Reconcile command order and changed-path-to-test map. | Validation ledger, stale/not-run scope, negative evidence, residual risk. | `validation-broker`, `execution-trajectory-analysis` | Handoff cites tests for code they never exercised. |

# Selection Rules

Select this capability over `unit-testing` when the design of the seam itself is unclear. Select it with `quality-test-gate` when test depth, assertion strength, fixture ownership, or stale validation affects closure. Select it with `contract-testing` when a fake, stub, or mock represents an external contract. Select it with `integration-testing` when the seam needs one real-boundary verification. Select it with `dependency-wiring-lifecycle` when test overrides affect construction, singletons, DI containers, provider graphs, or service locators. Select it with `data-side-effect-flow-tracing` when pure-looking code reads clock/env/random/process state or performs hidden IO. Select it with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when graph edges, stale memory, command order, or validation freshness affect seam claims.

# Proactive Professional Triggers

- **Signal:** A test imports or requests export of `_private`, `private*`, local mapper, hook internals, helper-only file, or package-private method. **Hidden risk:** test locks implementation and forces public API pollution. **Required professional action:** find public behavior boundary or reject visibility widening. **Route to:** `implementation-structure-design`, `quality-test-gate`. **Evidence required:** public boundary, rejected export, behavior assertion or no-test rationale.
- **Signal:** A test verifies internal call order, private method calls, or mock choreography while user-visible or state-visible behavior is untested. **Hidden risk:** implementation can be wrong while mock expectations pass. **Required professional action:** replace with public outcome assertion or record limitation. **Route to:** `code-clarity-maintainability`, `quality-test-gate`. **Evidence required:** behavior assertion, removed private mock, residual risk.
- **Signal:** A fake, stub, or mock stands in for HTTP, DB, queue, cache, file, SDK, auth provider, generated client, or external service without contract/integration proof. **Hidden risk:** test double drifts from real provider. **Required professional action:** add contract, calibration, or real-boundary check. **Route to:** `contract-testing`, `integration-testing`. **Evidence required:** contract source, provider check, double limitations.
- **Signal:** Tests patch globals, monkeypatch containers, mutate singletons, replace private modules, or build alternate dependency graphs. **Hidden risk:** test graph differs from production and hides lifecycle bugs. **Required professional action:** define explicit override seam and reset semantics. **Route to:** `dependency-wiring-lifecycle`, `repository-graph-analysis`. **Evidence required:** graph variant, override owner, reset/cleanup path, validation command.
- **Signal:** Wall clock, random, UUID, locale, timezone, sleep, async timing, process state, env vars, feature flags, or scheduler behavior affects assertions. **Hidden risk:** flaky, unreproducible, or environment-dependent tests. **Required professional action:** introduce deterministic source and record default/test behavior. **Route to:** `test-data-management`, `regression-testing`. **Evidence required:** deterministic control map, seed/frozen time, flake mitigation.
- **Signal:** Shared fixtures, object mothers, snapshots, golden files, or broad test builders carry business data across modules. **Hidden risk:** hidden coupling and unrelated test churn. **Required professional action:** assign owner, narrow fields, and deletion/update path. **Route to:** `test-data-management`, `implementation-structure-design`. **Evidence required:** fixture owner, fields asserted, mutation policy, validation.
- **Signal:** Refactor starts before characterization tests on untested, complex, auth, data, financial, concurrency, or stateful behavior. **Hidden risk:** structure change smuggles behavior change. **Required professional action:** characterize current public behavior before movement. **Route to:** `refactoring`, `regression-testing`. **Evidence required:** characterization tests, behavior boundary, command output.
- **Signal:** Validation evidence predates seam, fixture, mock, generated input, or public boundary changes. **Hidden risk:** stale tests support an untested final diff. **Required professional action:** broker validation freshness and rerun or disclose partial proof. **Route to:** `validation-broker`, `execution-trajectory-analysis`. **Evidence required:** changed-path-to-test map, command order, freshness verdict.

# Risk Escalation Rules

Escalate to `quality-test-gate` when test layer selection, fixture ownership, assertion strength, flaky risk, validation freshness, or no-test rationale is unresolved. Escalate to `integration-change-builder`, `data-middleware-change-builder`, or `backend-change-builder` when the seam crosses HTTP, DB, queue, cache, file, clock, environment, SDK, provider, or side-effect boundaries. Escalate to `security-privacy-gate` when seams affect auth, tenant isolation, permission, secrets, PII, redaction, or security-sensitive defaults. Escalate to `language-testing-strategy` when runtime-specific tools such as race detectors, mutation testing, property-based testing, fake timers, async test harnesses, or sanitizer builds are needed. Escalate to `reliability-observability-gate` when tests must prove concurrency, timers, background loops, retries, or shutdown behavior.

# Reference Loading Policy

Current mode is inline-only: this capability has no deep reference files today, so this `SKILL.md` contains the active seam-design rules.

If deep references are added later, load them only for L3+ work, AI-generated tests, private-helper export pressure, unclear public behavior boundaries, external contract doubles, uncontrolled time/randomness/IO risks, dependency graph overrides, flaky repair, characterization-test planning, or validation freshness disputes.

Do not load deep references for L1/L2 local changes where the output contract can be satisfied from the inline public-boundary, seam map, deterministic-test, fixture-owner, and validation-freshness rules.

# Critical Details

- Public behavior boundary: API endpoint, service method, component behavior, CLI command, job outcome, repository contract, event contract, module facade, generated client contract, or user-visible state.
- Test seam: injected dependency, factory, provider, adapter interface, fake clock, random/UUID provider, environment reader, file system adapter, queue producer, cache gateway, repository, SDK client, scheduler, or test graph override.
- Fake: working in-memory replacement for a boundary when stateful behavior matters; must be calibrated when the real provider has constraints.
- Stub: fixed response for a simple dependency outcome; must include error/edge cases when behavior branches on them.
- Mock: interaction verification for an external boundary only when the interaction is the behavior; avoid private choreography assertions.
- Spy: passive call recording when observable state is insufficient and the boundary is external or explicitly declared.
- Contract tests verify that test doubles match real providers; unit tests verify local rules; integration tests verify real boundary behavior; E2E tests verify full user journeys.
- Characterization tests capture current behavior before refactor, including bugs when the refactor must preserve them until a separate bug fix.
- Test data builders belong to the owning domain or module test boundary; broad shared fixture factories need a pure technical reason and owner.
- Mutation testing is triggered by critical branching or calculations. Property-based testing is triggered by invariant-rich input spaces, parsers, normalization, money/time math, and algorithms with many equivalent classes.
- Flaky risk appears when tests depend on wall clock time, random ordering, real sleeps, network timing, shared ports, global state, parallel mutation, uncontrolled schedulers, or mutable fixtures.
- A seam that makes production code harder to reason about must be justified by a real boundary or rejected as test-only architecture.

# Failure Modes

- Exporting `_calculateDiscount`, `privateNormalize`, a hook helper, or a local mapper only so tests can import it.
- Mocking internal call order while public behavior is untested.
- Using a mock for a database, HTTP provider, queue, auth provider, SDK, or cache without contract or integration evidence.
- Tests patch module globals, singleton containers, or private registry state and pass against a graph production cannot build.
- Sharing a fixture factory across modules until a local change breaks unrelated tests.
- Using real wall clock time, random UUIDs, sleeps, current locale/timezone, external services, or shared ports in tests.
- Refactoring first and adding characterization tests later.
- Treating snapshot, golden update, or mock call count as proof without naming the behavior protected.
- Reporting validation as current after fixture, seam, mock, generated input, or public-boundary changes.

# Output Contract

Return a `testability_seam_plan` with:
- `public_behavior_boundary`: behavior under test, public entry point, observable outputs/side effects, and private-helper non-export decision.
- `seam_inventory`: dependencies, nondeterministic inputs, side effects, global state, dependency graph overrides, fixtures, generated inputs, and owner for each seam.
- `test_double_decision`: fake/stub/mock/spy/real-boundary choice, why that double can fail for the risk, rejected doubles, and contract/integration calibration.
- `deterministic_controls`: time, randomness, UUID, locale/timezone, concurrency, scheduler, environment, feature flag, IO, network, DB/cache/queue strategy.
- `fixture_and_builder_ownership`: fixture/factory/seed/golden owner, fields asserted, mutation policy, privacy/determinism boundary, and update/delete path.
- `minimal_verification_decision`: smallest sufficient public-boundary check, rejected heavier/lighter tests, and risk reason for broader integration/contract/E2E proof when required.
- `test_split`: unit, integration, contract, regression, property-based, mutation, and E2E responsibilities with what each proves and does not prove.
- `characterization_plan`: current behavior to lock before refactor, fixture inputs, expected outputs, bugs preserved, and command to run before movement.
- `graph_memory_execution_validation`: repository graph edges inspected, memory claims accepted/rejected, execution order/freshness, validation map, negative evidence, and residual risk.
- `rejected_testability_shortcuts`: private export, over-mock, global patch, shared fixture, snapshot/golden-only, sleep/retry, or test-only interface rejected with reason.

# Evidence Contract

Close the plan only when these answers are concrete:
- **Basis:** behavior boundary under test, risk being proven, and why a seam is needed.
- **Encapsulation:** private-helper non-export decision, visibility/placement conflicts, and rejected test-only architecture.
- **Fidelity:** dependencies replaced by seams, test-double choices, real-provider contract/integration evidence, and double limitations.
- **Determinism:** time/random/UUID/concurrency/env/IO controls, fixture ownership, reset/cleanup, and flake mitigation.
- **Graph and memory:** current source, graph edges, fixture/mock/generator owners, accepted/rejected memory claims, and stale-context limits.
- **Validation:** command outcomes, freshness, stale/not-run scope, changed-path-to-test map, what evidence proves and does not prove, residual flake/integration risk, and next gate.

# Benchmark Coverage

This capability covers public-behavior testing, private-helper non-export, test double selection, mock/fake fidelity, contract and integration calibration, deterministic clock/random/UUID/env controls, concurrency scheduling seams, dependency graph overrides, fixture ownership, characterization tests, property/mutation trigger decisions, flake mitigation, graph-memory-trajectory reconciliation, validation freshness, and evidence-limited handoff.

# Routing Coverage

Routes from `change-forge-router`, `quality-test-gate`, `backend-change-builder`, `frontend-change-builder`, `integration-change-builder`, `data-middleware-change-builder`, `ai-code-review-refactor`, `refactoring`, `implementation-structure-design`, `dependency-wiring-lifecycle`, `data-side-effect-flow-tracing`, and `test-data-management` should arrive here when test seam design, public behavior boundary, private helper export pressure, over-mocked internals, fixture ownership, deterministic input control, dependency graph override, characterization tests, or validation freshness of seam evidence is at issue. Route away when the primary need is broad test strategy, real-boundary integration design, consumer contract design, E2E journey coverage, or test data privacy/cleanup without a seam decision.

# Quality Gate

1. Public behavior boundary is named, and tests use it by default.
2. Private helpers are not exported, split, or made visible only for testing.
3. Every seam has production purpose, external boundary, nondeterministic source, lifecycle owner, or explicit test boundary.
4. Minimal checks are matched to risk; trust-boundary, contract, data, concurrency, security, accessibility, and release risks retain broader proof.
5. Mocks do not assert private call order unless no public boundary can expose behavior and that limitation is recorded.
6. External systems have explicit fake, stub, mock, spy, contract, or integration strategy with fidelity evidence.
7. Time, randomness, UUIDs, concurrency, environment, feature flags, schedulers, and IO are deterministic in tests.
8. Fixture, builder, seed, snapshot, and golden ownership and reason to change are explicit.
9. Characterization tests exist before risky refactors.
10. Dependency graph overrides preserve production semantics and have reset/cleanup strategy.
11. Flaky risks have mitigation or named residual risk.
12. Graph, memory, execution trajectory, validation freshness, negative evidence, and changed-path-to-test mapping are reconciled before closure.

# Used By

- quality-test-gate
- backend-change-builder
- frontend-change-builder
- integration-change-builder
- data-middleware-change-builder
- ai-code-review-refactor

# Handoff

Hand off to `quality-test-gate` for test depth, `implementation-structure-design` for visibility or placement conflicts, `contract-testing` for external contract doubles, `integration-testing` for real-boundary proof, and `language-testing-strategy` for runtime-specific test tooling.

# Completion Criteria

The capability is complete when code can be verified through observable behavior, every non-deterministic or external dependency has a controllable seam, test doubles are chosen by contract need, private helpers remain private, fixtures have owners, and validation evidence or residual risk is explicit.
