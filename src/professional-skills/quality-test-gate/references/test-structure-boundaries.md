# Test Structure Boundaries

Use this reference when a change adds test helpers, fixtures, factories, golden files, mocks, or tests around refactored structure. It is loaded for testing, code-review, and refactoring cases where test organization may hide module ownership or assert internals instead of behavior.

## Test Placement Decision Tree

1. Identify the owning module.
   - Unit tests sit with the unit or module convention.
   - Integration tests sit at the integration boundary.
   - Contract tests sit with the contract owner or consumer/provider convention.

2. Match the production boundary.
   - If production code is split into submodules, tests and fixtures should usually split with the same ownership.
   - A large module split that leaves all tests in one shared directory is incomplete unless local convention requires it.

3. Reject private-helper testing.
   - Tests should assert public behavior or module-visible contracts.
   - Private helper tests are acceptable only for pure algorithmic units with no better public boundary and should not freeze implementation structure.

## Fixture And Helper Ownership

- Fixture, factory, mock, and golden data belong to the module whose behavior they represent.
- Shared test utilities must be pure technical helpers: builders, clock controls, temp directories, HTTP test harnesses, or assertion helpers with no business vocabulary.
- Business fixtures such as order cancellation, refund, tenant entitlement, invoice state, or permission role data belong in the owning module's test boundary.
- A shared helper with domain terms is a test-structure smell and should be moved or renamed with ownership.

## Mock Boundary Rules

- Mock external systems, public module APIs, time, randomness, and slow side-effect boundaries.
- Do not mock internal implementation details created by a refactor; test through observable behavior.
- If a mock encodes provider behavior, validate the assumption with contract or integration evidence.

## Test Readability Rules

- Test names express business behavior, not method implementation.
- Non-trivial tests explain the scenario, regression, fixture contract, or edge case.
- Golden files state which contract they represent and who owns updates.
- Test helpers should reduce setup noise without hiding the behavior under test.

## Required Evidence

Record:

- Test location and owning module.
- Fixture/factory/mock/golden owner.
- Public behavior or contract under test.
- Private helper access rejected or justified.
- Mock boundary and validation evidence.
- Test directory impact when module boundaries split.
