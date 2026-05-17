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

# Non-Negotiable Rules

- **Test observable behavior and business rules, not private implementation mechanics.** A test that asserts "the private method `_buildQuery` was called with these arguments" is testing implementation — if the private method is renamed or inlined, the test breaks for zero safety benefit. Tests must assert: what value was returned, what state was changed, what error was thrown, or what event was emitted. If the correct behavior can be observed only through private state, the design has an encapsulation problem.
- **Cover boundary values, invalid inputs, edge cases, and error paths — not only the happy path.** The happy path test proves only that the code works when all inputs are valid and the environment is cooperative. A business rule with no boundary or negative tests is a rule with unknown behavior at the edges. Required coverage for any non-trivial function: (1) the expected success case with a representative input; (2) the boundary values at the edges of valid input ranges (0, 1, max, max+1, negative); (3) invalid inputs that should be rejected (null, empty, wrong type, malformed format); (4) the expected error cases (insufficient funds, duplicate entry, rate limit exceeded); (5) any edge cases noted in the business rule specification.
- **Every test must be deterministic, isolated, and independent of execution order.** A test that produces a different result on the second run (because it depends on a global counter that is incremented by the first run) is not a unit test — it is a liability. Required: each test must set up all the state it needs (no shared mutable state between tests); must not depend on the execution order of other tests; must not depend on wall clock time, network state, or random number generator output unless these are explicitly mocked or seeded.
- **Mock only at meaningful architectural boundaries, not at every collaborator.** Over-mocking produces tests that pass even when the integration of the actual components is broken. The rule: mock at the boundary of the unit under test — the layer where the real implementation introduces nondeterminism (network), slowness (database), side effects (email), or test environment unavailability (external API). Do not mock value objects, pure functions, or internal helpers that are part of the logic being tested.
- **Name tests by behavior and expected outcome, not by method name.** A test named `test_process()` tells the reader nothing. A test named `test_place_order__insufficient_funds__raises_InsufficientFundsError` communicates: the function under test, the condition, and the expected outcome. This name is also a specification: if the behavior changes, the test name is a documentation record of what changed. Follow the pattern: `[unit_under_test]__[condition]__[expected_outcome]` (or BDD: `given_X_when_Y_then_Z`).
- **Use table-driven or parameterized tests for rule matrices with many input/output combinations.** A business rule with 15 input categories and 15 expected outputs should not be 15 separate test functions — it should be a single parameterized test with a table of (input, expected_output) rows. This makes the coverage visible at a glance, makes adding new cases trivial, and prevents subtle duplication where 10 test functions share 80% of the same setup code.

# Industry Benchmarks

Anchor against: **Kent Beck — Test-Driven Development** — red-green-refactor; test list before implementation; one failing test at a time. **Robert C. Martin (Uncle Bob) — Clean Code / The Clean Coder** — test per behavior; FIRST principles (Fast, Isolated/Independent, Repeatable, Self-Validating, Timely). **Gerard Meszaros — xUnit Test Patterns** — test doubles (stub, mock, fake, spy); fixture strategies; assertion patterns. **Boundary Value Analysis and Equivalence Partitioning (ISTQB)** — systematic derivation of test inputs that maximize defect detection with minimal test count. **Mutation Testing (PIT Mutation Testing, Stryker)** — mutant operators (change `>` to `>=`; negate condition; remove statement); survived mutants reveal tests that pass even when the code is wrong. **Property-Based Testing (Hypothesis, fast-check, QuickCheck)** — automatically generate hundreds of inputs to find edge cases; specify invariants that must hold for all valid inputs. **Google Testing Blog** — "Testing on the Toilet" series; prefer testing behavior over implementation; avoid testing private methods; test size definitions (small, medium, large). **Jest / Vitest / pytest / JUnit 5 / RSpec** — parametrize decorators (`@pytest.mark.parametrize`, `test.each`, `where:`); `describe`/`it` hierarchy for behavior organization.

### Unit Test Case Design Matrix

```
Business Rule: "Order discount is applied as follows:
  - Cart total < $50: no discount
  - $50 ≤ total < $100: 5% discount
  - $100 ≤ total < $200: 10% discount
  - total ≥ $200: 15% discount
  - Discount never exceeds the cart total"

Test Matrix:
Test Case ID | Input (total) | Expected Discount | Category
-------------|---------------|-------------------|-----------------------------
TC-01        | $0.00         | $0.00             | Boundary: empty cart
TC-02        | $49.99        | $0.00             | Boundary: just below 5% tier
TC-03        | $50.00        | $2.50             | Boundary: exact 5% tier entry
TC-04        | $75.00        | $3.75             | Representative: middle of 5% tier
TC-05        | $99.99        | $4.99             | Boundary: just below 10% tier
TC-06        | $100.00       | $10.00            | Boundary: exact 10% tier entry
TC-07        | $199.99       | $19.99            | Boundary: just below 15% tier
TC-08        | $200.00       | $30.00            | Boundary: exact 15% tier entry
TC-09        | $1000.00      | $150.00           | Representative: large order
TC-10        | -$10.00       | IllegalArgumentException | Edge: negative total
TC-11        | null          | NullPointerException / 400 | Edge: null input
```

### Dependency Control Strategy

```typescript
// What to mock: external boundary (HTTP client, email sender, repository)
// What NOT to mock: internal logic collaborators

// GOOD: mock at the repository boundary (DB call is the nondeterminism)
describe('OrderService.placeOrder', () => {
  it('raises InsufficientFundsError when balance is below order total', () => {
    const mockAccountRepo = { findById: jest.fn().mockResolvedValue({ balance: 10 }) };
    const service = new OrderService(mockAccountRepo);
    await expect(service.placeOrder({ accountId: '1', total: 50 }))
      .rejects.toThrow(InsufficientFundsError);
  });
});

// BAD: mock the internal calculation — tests nothing about the rule
describe('OrderService.placeOrder', () => {
  it('calls _calculateDiscount', () => {
    const spy = jest.spyOn(service as any, '_calculateDiscount');
    await service.placeOrder({ total: 100 });
    expect(spy).toHaveBeenCalled(); // proves choreography, not correctness
  });
});
```

# Selection Rules

Select this capability when **the risk is localized to a domain logic function, algorithm, validator, or transformer that has no real external dependencies**. Route to `integration-testing` when correctness depends on real database queries, ORM behavior, or real adapter behavior. Route to `contract-testing` when consumer-visible API or response schema compatibility is the risk. Route to `test-strategy` to decide which test levels are required for the overall change.

# Risk Escalation Rules

Escalate when: unit tests are the only test level for a change that involves a database state transition, external API call, or cross-service interaction (integration test is also required); a business rule enforces money movement, permission decisions, stock or quota limits, or state machine transitions and has zero boundary or negative test coverage (unacceptable coverage gap — must add); or a bug fix is applied without a regression test (the bug will likely reappear in the next refactor).

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

# Output Contract

Return a unit test plan with:

- `behaviors_under_test` (per changed rule/function: description, acceptance criterion trace)
- `test_case_matrix` (per behavior: input classes, boundary values, edge cases, error paths, expected outputs)
- `dependency_controls` (per external dependency: mock/stub/fake strategy; what is not mocked)
- `determinism_controls` (clock mock, random seed, global state reset strategy)
- `naming_convention` (template applied: `[unit]__[condition]__[expected]`)
- `parametrize_strategy` (which cases use table-driven tests; table format)
- `mutation_test_plan` (if applicable: mutation tool, threshold, CI gate)
- `evidence_command` (command to run the test suite and output coverage or pass/fail)

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
10. Mutation testing score (if run) is above the agreed threshold.

# Used By

- quality-test-gate
- backend-change-builder
- frontend-change-builder

# Handoff

Hand off to `test-strategy` for broader verification level decisions; `integration-testing` for real boundary behavior; `regression-testing` for locking defect-fix behavior; `test-data-management` for fixture and factory design.

# Completion Criteria

The capability is complete when **every changed business rule is protected by deterministic, isolated tests that cover its boundaries, edge cases, and error paths — and tests are anchored to observable behavior rather than implementation structure**.
