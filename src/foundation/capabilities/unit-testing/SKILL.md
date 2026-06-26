---
name: unit-testing
description: Designs unit tests for business rules, boundaries, edge cases, and error paths while avoiding tests anchored only to implementation details.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "59"
changeforge_version: 0.1.0
---

# Mission

**Prove local behavioral correctness through fast, deterministic, isolated tests that cover business rules, invariants, boundary values, edge cases, negative paths, and error paths** — making regressions visible within seconds of a code change, without relying on shared infrastructure, and without tests so anchored to implementation details that they break on every refactor while providing no behavioral safety net.

# When To Use

Use this capability when: a change adds or modifies domain logic, calculation algorithms, validation rules, business rule guards, state machine transition logic, data transformers, mappers, parsers, formatters, or local error handling; a change introduces a new function or class with non-trivial conditional logic; a bug is fixed and the fix must be locked against regression; a previously untested function is being refactored and a test net must be established before refactoring begins; or the test-strategy has designated unit testing as the primary verification level for a changed behavior.

# Do Not Use When

Do not use this capability when: correctness depends on real database queries, real HTTP connections, real message broker behavior, or real ORM behavior (use `integration-testing`); the primary concern is API contract compatibility across service versions (use `contract-testing`); the primary concern is an end-to-end user journey across multiple services (use `e2e-testing`).

# Stage Fit

Use during planning, implementation, bug-fix repair, refactoring, code review, and final validation when the risky claim can be proven through fast isolated behavior checks. In planning, identify the smallest behavior boundary and the input classes that can fail. In implementation, keep tests deterministic and close to the changed rule. In review, reject private-method, call-order, or mock-only assertions that do not prove behavior. In final handoff, map current source, repository graph, project memory, and execution trajectory to fresh test evidence and state what unit tests do not prove.

# Non-Negotiable Rules

- **Test observable behavior and business rules, not private implementation mechanics.** A test that asserts "the private method `_buildQuery` was called with these arguments" is testing implementation — if the private method is renamed or inlined, the test breaks for zero safety benefit. Tests must assert: what value was returned, what state was changed, what error was thrown, or what event was emitted. If the correct behavior can be observed only through private state, the design has an encapsulation problem.
- **Cover boundary values, invalid inputs, edge cases, and error paths — not only the happy path.** The happy path test proves only that the code works when all inputs are valid and the environment is cooperative. A business rule with no boundary or negative tests is a rule with unknown behavior at the edges. Required coverage for any non-trivial function: (1) the expected success case with a representative input; (2) the boundary values at the edges of valid input ranges (0, 1, max, max+1, negative); (3) invalid inputs that should be rejected (null, empty, wrong type, malformed format); (4) the expected error cases (insufficient funds, duplicate entry, rate limit exceeded); (5) any edge cases noted in the business rule specification.
- **Every test must be deterministic, isolated, and independent of execution order.** A test that produces a different result on the second run (because it depends on a global counter that is incremented by the first run) is not a unit test — it is a liability. Required: each test must set up all the state it needs (no shared mutable state between tests); must not depend on the execution order of other tests; must not depend on wall clock time, network state, or random number generator output unless these are explicitly mocked or seeded.
- **Mock only at meaningful architectural boundaries, not at every collaborator.** Over-mocking produces tests that pass even when the integration of the actual components is broken. The rule: mock at the boundary of the unit under test — the layer where the real implementation introduces nondeterminism (network), slowness (database), side effects (email), or test environment unavailability (external API). Do not mock value objects, pure functions, or internal helpers that are part of the logic being tested.
- **Name tests by behavior and expected outcome, not by method name.** A test named `test_process()` tells the reader nothing. A test named `test_place_order__insufficient_funds__raises_InsufficientFundsError` communicates: the function under test, the condition, and the expected outcome. This name is also a specification: if the behavior changes, the test name is a documentation record of what changed. Follow the pattern: `[unit_under_test]__[condition]__[expected_outcome]` (or BDD: `given_X_when_Y_then_Z`).
- **Use table-driven or parameterized tests for rule matrices with many input/output combinations.** A business rule with 15 input categories and 15 expected outputs should not be 15 separate test functions — it should be a single parameterized test with a table of (input, expected_output) rows. This makes the coverage visible at a glance, makes adding new cases trivial, and prevents subtle duplication where 10 test functions share 80% of the same setup code.

# Industry Benchmarks

Anchor against TDD red-green-refactor, FIRST test principles, xUnit Test Patterns, Boundary Value Analysis, Equivalence Partitioning, mutation testing, property-based testing, behavior-focused Google testing guidance, and framework-native parameterization in pytest, JUnit, Jest, Vitest, RSpec, and similar runners. Use [references/checklist.md](references/checklist.md) for quick planning and [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for case matrices, test-double choices, determinism controls, mutation/property triggers, and validation freshness patterns.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Pure rule or calculation | Algorithm, pricing, eligibility, validation, parser, mapper, formatter, or state guard with no real I/O. | Prove behavior through representative, boundary, invalid, and error cases. | Current source rule, table or property cases, expected outputs/errors. | `business-rule-extraction`, `failure-contract-design` | Integration setup for pure logic. |
| Bug-fix regression unit | Confirmed defect reproducible through one function/class/module boundary. | Preserve the exact failure trigger at the narrowest test level. | Red-before-fix or not-run reason, defect link, exact input/state, green-after-fix command. | `regression-testing`, `execution-trajectory-analysis` | Generic happy-path confirmation. |
| Refactor characterization | Untested code is being moved, extracted, renamed, or simplified. | Lock current observable behavior before changing structure. | Public behavior boundary, characterization cases, command before/after movement. | `testability-seam-design`, `plan-execution-consistency` | Private-helper export. |
| Determinism and seam repair | Clock, random, UUID, locale, timezone, env, globals, singleton, async timing, or generated input affects assertions. | Add explicit seams or controls without changing production semantics. | Deterministic control map, setup/teardown, reset or seed proof. | `testability-seam-design`, `test-data-management` | Real sleeps or order-dependent tests. |
| Assertion strength review | Tests assert call order, private fields, snapshots, or mocks while behavior remains unproved. | Replace choreography assertions with outcome assertions. | Behavior assertion, rejected implementation assertion, residual risk. | `ai-code-review-refactor`, `code-clarity-maintainability` | Snapshot/call-count-only evidence. |
| Validation freshness mapping | Reports, memory, graph, or prior run claims unit coverage after source/test/fixture/double changes. | Reconcile changed paths with current tests and rerun or downgrade evidence. | Changed-path-to-test map, command outcome, stale/not-run scope. | `validation-broker`, `repository-graph-analysis`, `project-memory-governance` | Trusting old green reports. |

# Selection Rules

Select this capability when **the risk is localized to a domain logic function, algorithm, validator, or transformer that has no real external dependencies**. Route to `integration-testing` when correctness depends on real database queries, ORM behavior, or real adapter behavior. Route to `contract-testing` when consumer-visible API or response schema compatibility is the risk. Route to `test-strategy` to decide which test levels are required for the overall change.

# Risk Escalation Rules

Escalate when: unit tests are the only test level for a change that involves a database state transition, external API call, or cross-service interaction (integration test is also required); a business rule enforces money movement, permission decisions, stock or quota limits, or state machine transitions and has zero boundary or negative test coverage (unacceptable coverage gap — must add); or a bug fix is applied without a regression test (the bug will likely reappear in the next refactor).

# Proactive Professional Triggers

- **Signal:** A changed business rule, calculation, validator, parser, mapper, or state transition has only a happy-path test. **Hidden risk:** boundary, invalid-input, and failure defects ship while coverage looks present. **Required professional action:** derive equivalence classes, boundary values, negative cases, and expected failures. **Route to:** `unit-testing`, `failure-contract-design`. **Evidence required:** case matrix, current source rule, assertion target, and command outcome or not-run reason.
- **Signal:** A unit test asserts a private helper, private field, mock call order, snapshot text, or internal choreography. **Hidden risk:** refactors break tests while wrong behavior can still pass. **Required professional action:** move proof to an observable public/module boundary or record why no boundary exists. **Route to:** `testability-seam-design`, `ai-code-review-refactor`. **Evidence required:** behavior assertion, rejected implementation assertion, and residual limitation.
- **Signal:** Clock, randomness, UUID, locale, timezone, global mutable state, singleton, scheduler, or async timing influences the result. **Hidden risk:** a flaky or environment-dependent unit test becomes noise and loses protection value. **Required professional action:** freeze, seed, inject, reset, or isolate the nondeterministic source. **Route to:** `testability-seam-design`, `test-data-management`. **Evidence required:** deterministic control map, setup/teardown, replay command, and flake residual risk.
- **Signal:** A bug fix is unit-testable but no test is shown red before the fix or linked to the defect. **Hidden risk:** the test may never have reproduced the recurrence path. **Required professional action:** capture the exact trigger and verify red/green evidence or document why red-before-fix cannot be produced. **Route to:** `regression-testing`, `execution-trajectory-analysis`. **Evidence required:** defect reference, input/state, pre-fix failure or limitation, final green command.
- **Signal:** A mock replaces the collaborator that carries the risk, such as persistence constraints, auth, queue semantics, provider payloads, or generated clients. **Hidden risk:** the unit test proves only the fake behavior and overclaims integration or contract safety. **Required professional action:** narrow the unit claim and add integration or contract proof for the real seam. **Route to:** `integration-testing`, `contract-testing`. **Evidence required:** mocked boundary, what the mock proves, what remains unverified, and next gate.
- **Signal:** Repository graph, project memory, prior validation, or generated reports say unit coverage exists after source, fixtures, doubles, generated inputs, or test commands changed. **Hidden risk:** stale evidence is reused for a different execution graph. **Required professional action:** reconcile current source and changed paths with fresh validation before closure. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `validation-broker`. **Evidence required:** accepted/rejected prior claim, changed-path-to-test map, command result, freshness verdict.

# Critical Details

- **A 100% line coverage metric does not mean 100% of rules are tested.** A test suite that executes every line once, all with valid happy-path inputs, can achieve 100% line coverage while leaving all boundary values, negative inputs, and error paths untested. Coverage metrics are development feedback, not a quality gate. The quality gate is: every changed rule has explicit boundary and failure coverage.
- **Tests that mirror implementation structure break on refactoring.** If every private method has its own test, refactoring the implementation to combine two private methods into one or to extract a helper class will break the tests — not because behavior changed, but because implementation structure changed. Tests must be anchored to the behavioral interface (inputs → outputs/errors/state), not to the internal call graph.
- **Deterministic test failures expose real bugs; flaky test failures destroy team trust.** A test that fails intermittently (due to uncontrolled randomness, uncontrolled clock, shared global state, or test ordering dependency) eventually gets marked as "known flaky" and ignored. A test that is ignored provides zero safety. Every test must be completely deterministic: mock `Date.now()`, seed `Math.random()`, reset global state in `beforeEach`, and never depend on test execution order.
- **Mutation testing reveals tests that pass even when the code is wrong.** A standard test run only verifies that the tests pass on the current code. Mutation testing (PIT, Stryker) introduces small changes to the production code (flip `>` to `>=`; negate a condition; remove a return statement) and verifies that the tests fail on the mutated code. "Survived mutants" are mutations that did not cause any test to fail — they identify business rules with insufficient test coverage.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `it('calls calculate()')` — asserts method was called | Proves choreography not correctness; breaks on refactor; no behavioral value | Assert: `expect(result.discount).toBe(10.00)` — what was returned |
| Only happy path test for a price calculation with 4 tiers | Three tiers untested; boundary values untested; bugs at tier boundaries ship | Table-driven test matrix covering all tiers and boundary values |
| `Math.random()` called in tested function without mocking | Test produces different assertion value on every run; intermittent failure | Mock random: `jest.spyOn(Math, 'random').mockReturnValue(0.5)` |
| Test directly accesses `obj._privateField` for assertion | Breaks on any refactor that changes internal storage | Redesign: test through public interface; if impossible, the API design is wrong |
| `jest.mock` on every collaborator including pure value helpers | Test passes even when the value helper is broken | Mock only at external boundaries (DB, HTTP, email); use real pure helpers |
| Bug fixed without regression test | Same bug re-introduced in next refactor; no test catches it | Write test that reproduces the bug first; confirm it fails; apply fix; confirm it passes |

# Failure Modes

- Business rule has only happy-path test: boundary bug ships to production uncaught.
- Test mocks internal calculation: refactor changes calculation; mocked test still passes; bug ships.
- Flaky test due to `Date.now()`: fails 1 in 100 runs; marked as flaky; ignored; real regression sneaks through.
- Error path not tested: error handler returns wrong HTTP status code; discovered in production by monitoring.
- No regression test on bug fix: same bug re-introduced 3 months later in a refactor.
- Over-broad mock: mock covers the validation logic; the validation is broken; test cannot detect it.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 routing, mode selection, output, and gates. Read [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete unit test plan. Read [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when selecting case matrices, comparing test-double choices, designing deterministic controls, deciding mutation/property triggers, reconciling graph-memory-execution evidence, or documenting validation freshness. Do not load deep references for a trivial pure-function assertion with obvious inputs, no fixture, no mock, no defect context, and no stale-validation dispute.

# Output Contract

Return a unit test plan with:

- `mode_selected` (pure rule/calculation, bug-fix regression unit, refactor characterization, determinism/seam repair, assertion strength review, or validation freshness mapping)
- `behaviors_under_test` (per changed rule/function: description, acceptance criterion trace)
- `source_evidence` (current source, existing tests, fixtures, repository graph, project memory, execution trajectory, and skipped evidence with reason)
- `test_case_matrix` (per behavior: input classes, boundary values, edge cases, error paths, expected outputs)
- `dependency_controls` (per external dependency: mock/stub/fake strategy; what is not mocked)
- `determinism_controls` (clock mock, random seed, global state reset strategy)
- `assertion_quality` (observable behavior asserted, rejected private/choreography assertions, and snapshot limits)
- `testability_seams` (public boundary, private-helper non-export decision, fixture owner, and deterministic seam owner)
- `naming_convention` (template applied: `[unit]__[condition]__[expected]`)
- `parametrize_strategy` (which cases use table-driven tests; table format)
- `mutation_test_plan` (if applicable: mutation tool, threshold, CI gate)
- `graph_memory_execution_coupling` (graph/memory/prior-run claims accepted, rejected, stale, partial, or not verified)
- `validation_freshness` (commands, exit codes, changed inputs covered, last material edit, stale/not-run status)
- `tool_permission_boundary` (shell/test runner/sandbox action class, permission state, local write or report outputs, and redaction rule)
- `evidence_scope` (what the unit run proves, what it explicitly does not prove, and any overclaim risk)
- `residual_unit_test_risk` (uncovered integration, contract, concurrency, data, security, performance, or production-runtime behavior and next gate)

# Evidence Contract

A unit test is accepted only when the output includes:

- **Unit boundary**: function/class/module under test and dependencies excluded.
- **Behavior under test**: observable input/output, state transition, error, or side effect.
- **Source basis**: current source/test/fixture paths, repository graph or memory leads accepted/rejected, and stale context limitations.
- **Mock boundary**: which collaborators are mocked and why mocking does not hide the defect or risk boundary.
- **Assertions**: behavior-oriented assertions, not private implementation assertions.
- **Negative path**: invalid input, denied case, exception, or edge case when relevant.
- **Fixture ownership**: test data owner, setup/teardown, and isolation.
- **Validation evidence**: command, exit code, output artifact or not-run reason, changed inputs covered, and freshness after final material edit.
- **What evidence proves**: the named isolated behavior, branch, invariant, failure path, or regression trigger is protected.
- **What evidence does not prove**: integration wiring, persistence, network, browser, concurrency, production config, external contract, load behavior, or unrelated release readiness.
- **Tool boundary**: test runner or shell action class, sandbox/permission status, generated-output scope, and sensitive-output redaction.
- **Residual risk**: untested integration or runtime behavior and next gate.

# Quality Gate

The unit test plan is complete only when:

1. Every changed business rule has a test case matrix covering success, boundary, invalid input, and error paths.
2. Tests assert behavioral outcomes (return values, thrown errors, state changes), not internal call sequences.
3. All tests are deterministic (clock, random, global state controlled).
4. Mocks are applied only at external boundaries (not to internal logic collaborators).
5. Test names follow the `[unit]__[condition]__[expected]` or BDD pattern.
6. Table-driven tests are used for rules with 5+ input/output combinations.
7. Every bug fix has a regression test written before the fix is applied.
8. Test suite runs in < 30 seconds (if it exceeds this, identify slow tests and convert to integration tests or use in-memory fakes).
9. No test depends on shared mutable state or execution order.
10. Graph, memory, and prior validation claims are confirmed against current source or downgraded before handoff.
11. Validation evidence names command, exit code, changed inputs covered, freshness after final edit, and not-run/stale scope.
12. Unit-test evidence does not overclaim integration, contract, security, concurrency, performance, production configuration, or external-provider proof.
13. Tool permission/sandbox boundaries are recorded when shell commands, generated reports, build artifacts, or secret-sensitive output are involved.
14. Mutation testing score (if run) is above the agreed threshold.

# Benchmark Coverage

This capability covers behavior-oriented unit tests, TDD red-green-refactor, FIRST principles, xUnit test doubles, boundary-value and equivalence-class design, table-driven and parameterized tests, deterministic clock/random/UUID/global controls, mutation and property-based trigger decisions, private-helper non-export, regression unit evidence, assertion-strength review, graph-memory-execution reconciliation, validation freshness, and evidence-limited handoff.

# Routing Coverage

Route here when the primary risk is local behavior inside a pure function, module, service method, validator, parser, mapper, formatter, policy, algorithm, or state guard. Route away when the primary proof requires real persistence, framework wiring, queue/cache/provider behavior, auth filter execution, consumer-visible compatibility, browser/user journey, fixture privacy/cleanup strategy, or broad test-level selection.

# Used By

- quality-test-gate
- backend-change-builder
- frontend-change-builder

# Handoff

Hand off to `test-strategy` for broader verification level decisions; `integration-testing` for real boundary behavior; `contract-testing` for consumer-visible compatibility; `regression-testing` for locking defect-fix behavior; `testability-seam-design` for private-helper, mock, deterministic input, or public-boundary conflicts; `test-data-management` for fixture and factory design; and `validation-broker` for changed-path-to-test freshness.

# Completion Criteria

The capability is complete when **every changed business rule is protected by deterministic, isolated tests that cover its boundaries, edge cases, and error paths — and tests are anchored to observable behavior rather than implementation structure**.
