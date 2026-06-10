---
name: testability-seam-design
description: Designs observable behavior test boundaries and explicit test seams without exporting private helpers or over-mocking internals; use when code needs deterministic tests across collaborators, time, randomness, concurrency, or external IO.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "107"
changeforge_version: 0.1.0
---

# Mission

Design code so its public behavior can be tested directly, while external systems and non-deterministic inputs are controlled through explicit seams that do not weaken encapsulation.

# When To Use

Use when tests require fakes, stubs, mocks, spies, fixtures, generated data, deterministic clocks, random values, UUIDs, concurrency scheduling, environment variables, files, HTTP, databases, queues, caches, or SDK clients.

Use before risky refactors when characterization tests are needed to lock current observable behavior before moving code.

# Do Not Use When

Do not use to justify testing private helpers directly, exporting internals, or adding interfaces that have no production boundary or test seam.

Do not use when the change is a no-behavior edit and existing tests already prove the public contract.

# Non-Negotiable Rules

- Test through observable public behavior by default.
- Mock only external boundaries or explicitly declared seams.
- Do not mock private implementation details.
- Do not make private code public, exported, or package-visible only for tests.
- Every new seam must have production purpose or a clear test boundary.
- Fixtures must have an owner and a reason to change.
- Characterization tests must precede risky refactors.
- Time, randomness, concurrency, and external IO must be controllable in tests.

# Industry Benchmarks

Anchor against xUnit public behavior testing, London versus classical test double tradeoffs, consumer-driven contract testing, Michael Feathers characterization tests, property-based testing for invariant-heavy logic, mutation testing for critical calculations, and Testing Library guidance that tests should resemble user-visible behavior rather than implementation details.

# Selection Rules

Select this capability over `unit-testing` when the design of the seam itself is unclear. Select it with `contract-testing` when a fake or mock represents an external contract. Select it with `integration-testing` when the seam needs one real-boundary verification. Select it with `implementation-structure-design` when a proposed file split, export, or helper exists only to make private code testable.

# Risk Escalation Rules

Escalate to `quality-test-gate` when test layer selection, fixture ownership, or flaky risk is unresolved. Escalate to `integration-change-builder`, `data-middleware-change-builder`, or `backend-change-builder` when the seam crosses HTTP, DB, queue, cache, file, clock, or environment boundaries. Escalate to `language-testing-strategy` when runtime-specific tools such as race detectors, mutation testing, property-based testing, or fake timers are needed.

# Reference Loading Policy

Current mode is inline-only: this capability has no deep reference files today, so this `SKILL.md` contains the active seam-design rules.

If deep references are added later, load them only for L3+ work, AI-generated tests, private-helper export pressure, unclear public behavior boundaries, external contract doubles, or uncontrolled time/randomness/IO risks.

Do not load deep references for L1/L2 local changes where the output contract can be satisfied from the inline public-boundary, seam map, and deterministic-test rules.

# Critical Details

- Public behavior boundary: API endpoint, service method, component behavior, CLI command, job outcome, repository contract, event contract, or module facade.
- Test seam: injected dependency, factory, provider, adapter interface, fake clock, random/UUID provider, environment reader, file system adapter, queue producer, cache gateway, or database repository.
- Fake: working in-memory replacement for a boundary when stateful behavior matters.
- Stub: fixed response for a simple dependency outcome.
- Mock: interaction verification for an external boundary only when the interaction is the behavior.
- Spy: passive call recording when observable state is insufficient and the boundary is external or explicitly declared.
- Contract tests verify that test doubles match real providers; unit tests verify local rules; integration tests verify real boundary behavior.
- Characterization tests capture current behavior before refactor, including bugs when the refactor must preserve them until a separate bug fix.
- Test data builders belong to the owning domain or module test boundary; broad shared fixture factories need a pure technical reason.
- Mutation testing is triggered by critical branching or calculations. Property-based testing is triggered by invariant-rich input spaces, parsers, normalization, money/time math, and algorithms with many equivalent classes.
- Flaky risk appears when tests depend on wall clock time, random ordering, real sleeps, network timing, shared ports, global state, parallel mutation, or uncontrolled schedulers.

# Failure Modes

- Exporting `_calculateDiscount`, `privateNormalize`, or a local mapper only so tests can import it.
- Mocking internal call order while public behavior is untested.
- Using a mock for a database, HTTP provider, queue, or cache without contract or integration evidence.
- Sharing a fixture factory across modules until a local change breaks unrelated tests.
- Using real wall clock time, random UUIDs, sleeps, or external services in tests.
- Refactoring first and adding characterization tests later.
- Treating snapshot or golden updates as proof without naming the behavior protected.

# Output Contract

Return a Testability Seam Plan:

- Public behavior boundary.
- Dependency seam map.
- Mock, fake, stub, and spy decision.
- Fixture ownership.
- Test data builder ownership and scope.
- Deterministic input, time, randomness, UUID, concurrency, environment, and IO strategy.
- Private-helper non-export decision.
- Contract, integration, and unit test split.
- Characterization test plan for risky refactors.
- Mutation testing or property-based testing trigger decision.
- Flaky risk and mitigation.
- Rejected testability shortcuts.

# Evidence Contract

Close the plan only when it names the behavior boundary under test, dependencies replaced by seams, files or modules inspected for existing test conventions, test-double choices and contract evidence, fixture owner, deterministic controls, validation command or not-run rationale, what the evidence proves and does not prove, residual flake or integration risk, and the next gate.

# Quality Gate

1. Public behavior tests exist or a no-test rationale is explicit.
2. Private helpers are not exported only for testing.
3. Mocks do not assert private call order unless no public boundary can expose behavior and that limitation is recorded.
4. External systems have explicit fake, stub, or contract test strategy.
5. Time, randomness, UUIDs, concurrency, environment, and IO are deterministic in tests.
6. Fixture ownership and reason to change are explicit.
7. Characterization tests exist before risky refactors.
8. Flaky risks have mitigation or named residual risk.

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
