---
name: quality-test-gate
description: Defines risk-based test strategy for product and code changes, including unit, integration, contract, E2E, migration, rollback, regression, fixture, mock, coverage, and manual verification expectations.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Quality Test Gate

## Mission
Define the minimum evidence needed to prove a change works correctly, does not regress critical behavior, handles failure paths, and can be safely released — by mapping test types, depth, fixtures, and mocks to explicit risks, not to arbitrary coverage targets, and by treating missing test evidence for high-risk changes as a blocking gate condition.

## When To Use
- Before code review, merge, or handoff when the test strategy for a change is undefined.
- When the right test level (unit, integration, E2E, contract, migration) is unclear.
- When fixture strategy, mock boundaries, or data setup for a change need to be designed.
- When migration scripts, rollback procedures, or database changes need test coverage.
- When a code change involves financial calculations, authorization, state machines, or safety-critical behavior.
- When regression risk from a cross-cutting refactoring is unclear.
- When a release gate requires test evidence that has not yet been produced.
- When an agent claims a fix is complete but supplies no command output, failing-before/passing-after evidence, or validator result.
- When product experiments, analytics events, exposure logging, or metric guardrails need verification.
- When ML model rollout, feature store changes, drift monitoring, fairness audits, or model rollback require validation.
- When monorepo affected-test selection, incremental build, build cache, or generated-file policies can hide regressions.

## Do Not Use When
- The change is trivial (renaming a variable, updating a comment) with zero behavior risk — demand evidence proportional to risk, not uniformly exhaustive.
- Test strategy is already defined in an accepted acceptance criteria document with complete coverage for all risks.

## Non-Negotiable Rules
- **Direct use still runs the runtime prompt flow.** When `quality-test-gate` is invoked directly and router reclassification is skipped, target-project engineering work must still clarify requirements before action, inspect relevant code/tests/config/docs before planning, name a TDD or validation signal before implementation, map each action to an owner skill and a different review skill, repair and re-review findings, and hand off with validation evidence, residual risk, and route/stage manifests when routed.
- **Map every material test to an acceptance criterion or a named risk** — tests without a justifying requirement or risk are noise; risks without a test are gaps.
- **Include negative path and failure mode coverage** when behavior changes — a test suite that only covers the happy path does not test the behavior, it tests the best case.
- **Mock boundaries must reflect real contracts**: mocks that return data the real dependency would never return create false confidence; consumer-driven contract tests or integration tests must validate mock assumptions.
- **Migration and rollback evidence is required for any data layer change**: a migration that has never been executed in a test environment is an untested production change.
- **Coverage percentages are not quality evidence**: 90% coverage with trivial assertions is worse than 60% coverage with contract and failure tests — coverage is a floor indicator, not a ceiling metric.
- **Test data must not include production PII or sensitive records**: use generated, anonymized, or synthetic data that represents realistic edge cases.
- **Flaky tests must be fixed or quarantined before merge**: a flaky test provides no signal and destroys trust in the test suite — merging known-flaky tests is not acceptable.
- **Concurrency and idempotency tests are required when code uses shared state, queues, or distributed writes**: race conditions that cannot be detected in sequential unit tests require explicit concurrency verification.
- **Experiment and model rollout tests require data validity checks**: exposure logging, sample ratio mismatch, feature point-in-time correctness, training-serving skew, drift metrics, and rollback version must be verified like code behavior.
- **Affected-test selection must be proven against a full-suite baseline**: monorepo speedups are valid only when module graph, dependency edges, cache keys, and generated inputs cannot skip impacted tests.
- **Agent-provided test evidence must be concrete**: accept command output, exit codes, logs, fixtures, screenshots, or recorded validator results; reject "tests should pass", undocumented local runs, and partial runs reported as full (a lint or type-check pass is not a test pass; one green test is not full-suite success).
- **Minimal validation is risk-bound**: L1 low-risk changes may use the smallest meaningful runnable check, but a smoke check is not evidence for money, security, auth, data migration, retry/idempotency, or production reliability correctness. Do not delete a meaningful smoke or self-check as bloat.
- **Test structure follows module structure**: test files, fixtures, factories, mocks, and golden data must have an owning module or contract boundary; shared test helpers must not become business-fixture dumping grounds.
- **Tests exercise public behavior by default**: refactors and splits are verified through public APIs, module contracts, or observable behavior, not private helper calls that freeze implementation details.

## Industry Benchmarks
- **Test Pyramid (Mike Cohn)**: Many unit tests, fewer integration tests, few E2E tests. Unit tests are fast and cheap; E2E tests are slow and expensive — invert the pyramid at your peril.
- **Testing Trophy (Kent C. Dodds)**: Emphasizes integration tests over unit tests for most product code — integration tests give the most confidence relative to cost when testing behavior rather than implementation.
- **Consumer-Driven Contract Testing (Pact)**: Consumers define the contract they depend on; providers verify against it. Catches integration breakage before deployment without end-to-end test fragility.
- **Google Testing Blog — Test Sizes (Small / Medium / Large)**: Small = no I/O, runs in milliseconds. Medium = some I/O (database, cache). Large = full system. Design the test suite to minimize the proportion of Large tests.
- **Mutation Testing (PITest / Stryker)**: Systematically introduces code mutations to verify that tests catch the mutation. A test suite that does not catch mutations is not actually testing the behavior.
- **NIST SP 800-115 (Technical Guide to Information Security Testing)**: Security test types — vulnerability scanning, penetration testing, code review. Applicable to security-critical test obligations.
- **Behavior-Driven Development (BDD / Gherkin — Cucumber)**: Given/When/Then acceptance scenarios written in business language — executable documentation that bridges specification and test.

### Test Level Selection Matrix

| Change Type | Minimum Test Coverage | When to Go Higher |
|---|---|---|
| Pure function, no I/O | Unit tests: normal, edge cases, error paths | Add property-based or mutation tests for critical calculations |
| Service layer with mocked dependencies | Unit tests + contract tests for mock assumptions | When mocks reflect real external contracts that change |
| Repository / database query | Integration test against real DB | Required for query plan and constraint verification |
| REST API endpoint | Integration test: auth, validation, success, 4xx, 5xx | Contract test if external consumers exist |
| User-facing flow (E2E path) | E2E smoke test for critical happy path | Add failure cases for payment, auth, destructive actions |
| Database migration | Migration test: forward + rollback + data integrity | Required for all production schema changes |
| Cross-service integration | Contract test (Pact) + sandbox integration test | When provider behavior cannot be reproduced locally |
| Security-critical path (auth, payment, data access) | Unit + integration + manual penetration test | Threat model determines additional coverage |

## Technical Selection Criteria
Select the appropriate evidence level for each risk category in the change:
- **Behavioral risk**: Does the change alter observable business logic (calculation, state transition, authorization decision)? Requires unit tests covering all logical branches, including error paths.
- **Integration risk**: Does the change call a real database, cache, queue, or external service? Requires integration tests (not just mocked) against real dependencies.
- **Contract risk**: Does the change modify an API or event schema that consumers depend on? Requires consumer-driven contract tests (Pact) or API contract tests (OpenAPI).
- **Migration risk**: Does the change include a database migration or data transformation? Requires migration forward test, rollback test, and data integrity assertion.
- **Regression risk**: Does the change touch cross-cutting code paths (middleware, auth, routing, shared utilities)? Requires regression test suite verification with no new failures.
- **Performance risk**: Does the change affect high-frequency queries, high-traffic endpoints, or large dataset operations? Requires query plan validation and optional load test.
- **Accessibility risk**: Does the change affect UI interactions for keyboard users or screen reader users? Requires axe-core accessibility scan and keyboard walkthrough.
- **Security risk**: Does the change affect authorization, authentication, input handling, or output encoding? Requires security-specific test cases and code review.
- **Experiment risk**: Does the change affect assignment, exposure logging, event taxonomy, funnel/cohort metrics, or guardrail rollback? Requires exposure tests, assignment stability checks, SRM checks, and dashboard/query validation.
- **Model risk**: Does the change affect a trained model, feature store, model registry, drift monitor, or fairness metric? Requires offline evaluation, online shadow/canary evidence, drift threshold, bias/fairness audit, and rollback model test.
- **Monorepo build risk**: Does affected-test selection or cache reuse decide what runs? Requires module graph validation, cache key review, generated-file policy checks, and periodic full-suite comparison.

## Mode Matrix
Select the testing mode by risk. Do not request tests generically; name the failure the test must catch.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| New behavior test strategy | New feature, endpoint, flow, schema, integration, job, or model. | Map material risks to unit/integration/contract/E2E/migration/load/security tests. | Risk-to-test map, fixture owner, what each test proves/does not prove. | `test-strategy`, matching implementation skill | Full E2E matrix for local logic. |
| Bug-fix regression | Defect, incident, failing test, same-pattern fix. | Prove the historical failure cannot recur and scan related cases. | Reproduction, regression test, same-pattern scope, old behavior preserved. | `regression-testing`, `agent-execution-discipline` | Snapshot-only regression proof. |
| Contract/API/migration test | Schema, DTO, event, migration, rollback, generated client. | Consumer compatibility, forward/rollback, version skew, data integrity. | Contract/migration commands, fixture data, consumer list. | `contract-testing`, `data-api-contract-changer` | Unit-only proof. |
| Integration/external dependency | DB/cache/queue/search/provider/webhook/file storage. | Mock-vs-real boundary, sandbox parity, retries, DLQ, reconciliation. | Real dependency or contract test, mock assumptions, failure simulation. | `integration-testing`, `integration-change-builder`, `data-middleware-change-builder` | Mock-only confidence. |
| Frontend/user behavior/a11y | UI form, route, component, focus, validation, disabled/error states. | User behavior, accessibility semantics, state coverage. | Accessibility-query assertions, axe/keyboard evidence, state matrix. | `frontend-testing`, `frontend-change-builder` | CSS selector/internal hook assertions. |
| Flaky/performance/security | Flaky CI, load/latency, auth, permission, calculation, race/idempotency. | Stabilize signal, cover negative cases, avoid false confidence. | Flake triage, property/negative cases, load/security evidence. | `security-privacy-gate`, `reliability-observability-gate` | Blind retries as a fix. |
| Minimal validation decision | L1 local change, simplicity-ladder decision, delete/shrink pass, or deliberate shortcut requests smaller evidence. | Choose the cheapest check that can fail for the real risk and reject under-testing for high-risk paths. | Risk classification, runnable check, what it proves/does not prove. | `minimal-correct-implementation`, `agent-execution-discipline` | Smoke check for security/auth/money/migration/retry/idempotency/reliability. |

## Proactive Professional Triggers

- **Signal:** bug fix has no test that fails before the fix or no stated historical failure. **Hidden risk:** missing regression proof means the test does not protect the bug. **Required professional action:** require reproduction or explain the non-automatable proof path. **Route to:** `regression-testing`, `agent-execution-discipline`. **Evidence required:** failing-before/passing-after test output or manual proof artifact with owner.
- **Signal:** API/schema/event change has only unit tests. **Hidden risk:** consumers or generated clients break. **Required professional action:** add contract or generated-client validation. **Route to:** `contract-testing`, `data-api-contract-changer`. **Evidence required:** contract test, schema diff, consumer impact.
- **Signal:** migration/backfill has no rollback and data-integrity assertion. **Hidden risk:** unrecoverable production state. **Required professional action:** test forward/rollback with representative data. **Route to:** `data-migration-design`, `delivery-release-gate`. **Evidence required:** migration test output and rollback proof.
- **Signal:** mocks replace real DB/cache/queue/provider behavior without contract validation. **Hidden risk:** tests validate impossible behavior. **Required professional action:** validate mock assumptions or use integration/sandbox test. **Route to:** `integration-testing`, `data-middleware-change-builder`, `integration-change-builder`. **Evidence required:** mock contract and failure cases.
- **Signal:** UI tests assert CSS/private internals instead of accessible user behavior. **Hidden risk:** accessibility failure or silent user-flow regression while tests pass. **Required professional action:** rewrite using accessibility queries and state assertions. **Route to:** `frontend-testing`, `code-clarity-maintainability`. **Evidence required:** accessible behavior assertion, axe/keyboard output, and state-coverage proof.
- **Signal:** flaky test is retried, skipped, or quarantined without owner/root cause. **Hidden risk:** real failure hidden by CI noise. **Required professional action:** triage flake before gate acceptance. **Route to:** `failure-diagnosis`, `agent-execution-discipline`. **Evidence required:** flake signature, owner, remediation.
- **Signal:** fixture/factory/golden file is shared across modules with business data and no owner. **Hidden risk:** hidden coupling and broad churn. **Required professional action:** assign fixture ownership or localize. **Route to:** `implementation-structure-design`, `code-clarity-maintainability`. **Evidence required:** owner, boundary, deletion/update path.
- **Signal:** tests require exporting private helpers, mocking internal call order, or reaching through module internals. **Hidden risk:** hidden implementation coupling and missing encapsulation boundary. **Required professional action:** require a public behavior boundary and explicit test seam. **Route to:** `testability-seam-design`, `implementation-structure-design`. **Evidence required:** seam map, private-helper non-export decision, and public-behavior test output.
- **Signal:** clock, randomness, UUIDs, concurrency, database, HTTP, queue, cache, file, or environment behavior is uncontrolled in tests. **Hidden risk:** missing reproducibility, stale test signal, or wrong failure diagnosis. **Required professional action:** require deterministic seams and classify fake/stub/contract/integration evidence. **Route to:** `testability-seam-design`, `dependency-wiring-lifecycle`. **Evidence required:** deterministic input map, external seam contract, fixture owner, and flake mitigation test output.
- **Signal:** negative-path tests cannot distinguish validation, permission, conflict, timeout, retryable, terminal, or partial failure states. **Hidden risk:** tests pass while boundary failure semantics remain ambiguous. **Required professional action:** test the failure contract at the right boundary. **Route to:** `failure-contract-design`, `backend-change-builder`. **Evidence required:** error taxonomy, translation map, and negative test output.
- **Signal:** tests cover a mapper/DTO/persistence model path where null/default/optional semantics can drift. **Hidden risk:** model boundary bugs are hidden behind happy-path fixtures. **Required professional action:** add mapping tests at the model boundary. **Route to:** `model-boundary-mapping`, `data-api-contract-changer`. **Evidence required:** mapping owner, null/default semantics, and compatibility cases.
- **Signal:** tests do not verify ordering for DB/cache/event/external IO side effects or hidden mapper/getter mutations. **Hidden risk:** behavior passes unit tests while transaction ordering, publish-after-commit, cache source of truth, or compensation is broken. **Required professional action:** require side-effect flow tests at the visible boundary. **Route to:** `data-side-effect-flow-tracing`, `integration-testing`. **Evidence required:** flow map, ordering test, source-of-truth assertion, and residual side-effect risk.
- **Signal:** public API, SDK, schema, event, or export change lacks old/new consumer compatibility tests. **Hidden risk:** local tests pass while downstream consumers break. **Required professional action:** add consumer impact and contract evidence. **Route to:** `consumer-impact-analysis`, `contract-testing`. **Evidence required:** consumer inventory, compatibility cases, generated-client check, migration/deprecation note, and telemetry plan.
- **Signal:** cleanup deletes flags, fallbacks, deprecated APIs, compatibility branches, or dead code without caller-search and rollback tests. **Hidden risk:** deletion removes runtime or generated references that ordinary unit tests miss. **Required professional action:** test cleanup/deletion governance before closure. **Route to:** `cleanup-deletion-governance`, `regression-testing`. **Evidence required:** caller search, telemetry or retained-risk decision, removed/preserved behavior tests, and rollback path.
- **Signal:** test confidence depends on import boundaries, generated-file policy, public/private exports, affected-test rules, or forbidden dependencies that are not enforced in CI. **Hidden risk:** missing CI enforcement lets tests be skipped or wrong architecture violations merge unnoticed. **Required professional action:** require architecture enforcement evidence or mark the test gate incomplete. **Route to:** `architecture-enforcement-tooling`, `ci-cd`. **Evidence required:** rule list, CI command, representative failure, generated-code exception, and affected-test proof.
- **Signal:** test plan lacks negative case for permission, idempotency, concurrency, invalid input, or partial failure. **Hidden risk:** missing negative-path regression leaves happy-path confidence only. **Required professional action:** add a mutation-like negative case for the named risk. **Route to:** `backend-change-builder`, `security-privacy-gate`, `data-middleware-change-builder`. **Evidence required:** denied/invalid/retry/partial-failure test output and what evidence proves.

### Decision Tree: Test Depth Required

```
Does the change modify a financial calculation, authorization decision, or safety-critical rule?
├── Yes → Unit tests for ALL branches + failure cases + property-based or mutation test required
Does the change modify a database schema or data migration?
├── Yes → Migration test (forward + rollback) + data integrity check required
Does the change modify a public API or event schema with known consumers?
├── Yes → Consumer-driven contract tests (Pact) required
Does the change involve an external integration (payment, identity, third-party API)?
├── Yes → Sandbox integration tests + failure simulation required
Does the change touch auth, session, or permission boundaries?
├── Yes → Security-specific test cases: boundary values, privilege escalation, session fixation
Does the change add or modify an A/B test or analytics metric?
├── Yes → Exposure logging test + assignment stability + SRM check + guardrail rollback test
Does the change roll out an ML model?
├── Yes → Offline eval + shadow/canary + drift/fairness checks + rollback model version test
Does the change use monorepo affected tests or build cache?
├── Yes → Module graph validation + cache key verification + generated file policy + full-suite fallback
Is the change a low-risk refactoring with no behavior change?
└── Run existing test suite; no new tests required if coverage is not reduced
```

## Risk Escalation Rules
- Escalate when financial or entitlement calculations have no property-based or exhaustive branch tests — edge case math errors are invisible until they cause financial loss.
- Escalate when a database migration lacks a rollback test — an untested rollback is not a rollback plan.
- Escalate when authorization rules have no test for the denied path — authorization tests that only cover the allowed path prove nothing about security.
- Escalate when concurrency scenarios (double-submit, race condition, duplicate event processing) have no test coverage and the code uses shared mutable state.
- Escalate when test mocks return data that the real dependency would never return — the test suite creates false confidence.
- Escalate when E2E tests are the only coverage for business-critical logic — E2E tests are too slow and fragile to be the primary regression safety net.
- Escalate when test data includes real production data — GDPR/privacy violation risk.
- Escalate when a known-flaky test is in the proposed merge — flaky tests mask real failures.
- Escalate when experiment launch lacks exposure logging tests, sample ratio mismatch detection, or guardrail rollback verification.
- Escalate when ML model rollout lacks model registry version pinning, training-serving skew checks, drift monitoring, fairness/bias audit, or rollback model verification.
- Escalate when monorepo affected-test selection has no full-suite comparison or cache keys omit lockfiles, generated inputs, or tool versions.
- Escalate to `agent-execution-discipline` when an agent closes a test gate without an evidence inventory or repeats the same failing test command twice without route repair.

## Critical Details
- **Test Doubles hierarchy**: Dummy (placeholder, never used) < Stub (returns canned response) < Fake (working implementation, e.g. in-memory DB) < Mock (verifies interactions) < Spy (records calls). Choose the simplest double that provides enough information.
- **Fixture isolation**: Each test must be able to set up and tear down its data independently. Tests that share mutable state are order-dependent and will fail in CI parallelism.
- **Snapshot tests as documentation, not assertions**: UI snapshot tests break on any cosmetic change — they should document intent, not gate behavior. Prefer behavioral assertions (accessible name, state presence) over full component snapshots.
- **`describe` / `it` naming discipline**: Test names should read as executable specifications: `it("rejects a payment when the account has insufficient funds")` is a specification. `it("test payment failure")` is noise.
- **The Test Pyramid inversion cost**: When E2E tests are primary, a single feature test takes 30+ seconds — a 500-test suite takes 4 hours. Teams stop running the suite. The feedback loop collapses.
- **Property-based testing for financial and calculation logic**: Use `Hypothesis` (Python), `fast-check` (TypeScript), or `QuickCheck` (Haskell/Elm) to generate random inputs that explore the full input space of a calculation — finds edge cases that example-based tests miss.
- **axe-core accessibility scan**: `jest-axe` and Playwright's built-in accessibility snapshot can be run as part of integration and E2E tests — catches WCAG violations automatically in CI.
- **Sample ratio mismatch test**: a statistically meaningful assignment count check should fail the experiment gate when observed allocation diverges from planned allocation beyond the declared threshold.
- **Training-serving skew test**: feature values used in offline training must match online serving semantics, including point-in-time joins, default values, null handling, and late-arriving data.
- **Build cache correctness test**: intentionally change a dependency, generated file input, lockfile, and test fixture in CI dry runs to prove the cache key invalidates the affected build/test shard.

## Test Structure Boundary Discipline

Tests are part of the implementation structure. When production code is split by object, file, or module boundary, test structure must either follow that boundary or explicitly justify a different local convention. Fixtures, factories, mocks, and golden files need owners; shared test utilities may hold pure technical helpers only. Load `references/test-structure-boundaries.md` when a change adds shared test helpers, tests private helpers, moves modules, or introduces business fixtures.

### Anti-Examples

| Test Approach | Problem | Corrected Approach |
|---|---|---|
| 95% line coverage, all tests mock database | Passes CI; production DB queries never tested | Integration tests against real DB for repository layer |
| E2E test for every business rule variant | 500 E2E tests, 4-hour CI pipeline | Unit tests for business logic; E2E for critical flows only |
| Migration runs in production, never tested | Rollback fails under pressure | Migration test environment; forward + rollback test before production |
| `expect(wrapper.find('.error-text').exists()).toBe(true)` | Tests CSS class, not behavior | `expect(screen.getByRole('alert')).toHaveTextContent('Invalid email')` |
| Mock returns `user.role = 'admin'` but real code never returns that value | Test validates a scenario that cannot happen | Contract test or integration test against real auth provider |

## Test Comment Discipline

Test comments are required when the test protects a non-obvious scenario:

- regression test for a prior bug;
- boundary or edge case;
- integration contract;
- concurrency/race behavior;
- retry/idempotency behavior;
- external provider quirk;
- migration/backfill behavior;
- security or permission denial;
- performance-sensitive behavior;
- golden fixture contract.

A test should not need comments for a trivial happy path when the test name is already precise. Prefer precise test names first, comments second.

## Failure Modes
- **Happy-path-only tests miss regressions**: a change that inadvertently breaks the error path ships to production undetected.
- **Excessive mocks validate fantasies**: the mock returns data the real service never returns — the test passes, production fails.
- **No rollback test hides migration failure**: the forward migration runs in staging; rollback is attempted in production after an incident; it fails because it was never tested.
- **Coverage percentage misleads**: 90% coverage with trivial assertions on getters and setters — 0 tests on the critical payment calculation; an off-by-one error ships.
- **Flaky test masks real failure**: a known-flaky test is retried 3 times in CI; on the day it matters, the real failure is hidden by the retry behavior.
- **Test data with production PII leaks**: a developer copies a production database export to use as a test fixture — the export includes customer email addresses and phone numbers in the repository.
- **E2E test for every rule variant**: 600 E2E tests run in sequence — CI takes 5 hours; engineers stop waiting for CI and merge without passing tests.
- **Concurrency untested**: a payment endpoint is called twice simultaneously from a client retry — both requests succeed due to a race condition; the customer is charged twice.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return a test strategy with:
- **Mode selected**: new behavior, bug-fix regression, contract/migration, integration, frontend/a11y, or flaky/performance/security, with trigger signal.
- **Boundaries inspected**: changed code paths, branches, public contracts, fixtures, mocks, generated files, DB/cache/queue/provider seams, UI states, CI selection, and release boundaries inspected or skipped with reason.
- **Professional judgment**: test depth decision, risk accepted or ruled out, and why cheaper or heavier evidence is insufficient or unnecessary.
- **Risk-to-test mapping**: Each identified risk paired with its required test type, depth, and pass criteria.
- **Proof statement**: for every proposed or executed test, what this test proves and what it does not prove.
- **Test level breakdown**: Unit / integration / contract / E2E / migration count and rationale.
- **Fixture strategy**: Data setup, isolation approach, and test data generation method.
- **Test structure strategy**: test file placement, fixture/factory/mock/golden ownership, public-behavior boundary, and shared helper audit.
- **Reuse and placement rationale**: why tests, fixtures, factories, mocks, golden files, and helpers live at their selected owner boundary.
- **Mock boundaries**: Which dependencies are mocked vs. real, and how mock assumptions are validated.
- **Testability seam plan**: public behavior boundary, dependency seam map, fake/stub/mock/spy decision, fixture ownership, deterministic time/randomness strategy, private-helper non-export decision, and rejected testability shortcuts.
- **Failure contract test split**: unit, contract, integration, and negative-path tests that prove retryable, terminal, validation, permission, conflict, timeout, cancellation, and partial-failure states.
- **Model mapping test obligations**: DTO/domain/persistence/event/view-model mapping cases, null/default/optional semantics, generated boundary cases, and compatibility fixtures.
- **Algorithm and scale test obligations**: input size, worst-case complexity, memory bound, streaming/chunking, benchmark/profile requirement, and scale-risk test evidence when the implementation is performance-sensitive.
- **Migration test plan**: Forward execution, rollback execution, and data integrity assertion approach.
- **Coverage obligations**: Specific logical branches or code paths that must be covered (not aggregate percentage).
- **Performance test obligations**: Query plan validation, load test threshold, or latency budget if applicable.
- **Accessibility test obligations**: axe-core coverage level, keyboard walkthrough, and screen reader test requirement.
- **Experiment test obligations**: exposure event assertion, assignment stability, sample ratio mismatch detection, primary/guardrail metric query validation, and rollback-on-guardrail regression evidence.
- **MLOps test obligations**: model version registry check, feature store point-in-time correctness, training-serving skew test, drift metric threshold, fairness/bias evaluation, shadow/canary plan, and rollback model verification.
- **Monorepo test obligations**: module graph, affected tests, cache key inputs, generated file policy, and full-test fallback cadence.
- **Validation evidence**: Commands run, exit codes, relevant output, artifacts produced, and any unrun test obligations with rationale.
- **Evidence limits**: what each test proves and what it does not prove about integration seams, scale, browsers, production data, flake risk, or release readiness.
- **Residual risks**: Accepted gaps with explicit business justification and mitigating controls.
- **Next gate/handoff**: implementation, contract, security, reliability, release, or no-next-gate rationale.

## Evidence Contract
Close a test strategy only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: the selected mode, risk-to-test mapping each test layer rests on, and why that layer is the right depth for the risk.
- **Files and boundaries inspected**: code paths, branches, public contracts, fixtures, mocks, generated files, integration seams, UI states, CI selection, and release boundaries the strategy covers, and the mock-versus-real boundary chosen for each dependency.
- **Placement rationale**: why each test sits at its level (unit/integration/contract/E2E/migration) instead of a cheaper or more expensive one.
- **Validation commands**: the literal test suites and validators run, each with its exit code, the obligation it satisfies, what evidence proves, and what evidence does not prove.
- **Testing judgment and handoff**: mode selected, risk-to-test judgment, behavior preservation when applicable, evidence limits, and next gate.
- **Residual risk**: the accepted coverage gap, flaky signal, mock limitation, untested negative case, or non-automatable obligation with its compensating manual evidence, and the named owner of the follow-up.

## Quality Gate
1. Every material risk has an identified test with pass/fail criteria.
2. Negative paths (error, denial, failure) are covered for all behavioral changes.
3. Migration tests cover forward execution, rollback execution, and data integrity.
4. Contract tests exist for all API or event schema changes with known consumers.
5. Authorization tests verify both the allowed and denied cases.
6. Mock assumptions are validated by contract or integration tests.
7. No production PII or sensitive records are used in test data.
8. No known-flaky tests are introduced without quarantine and a remediation ticket.
9. Financial and safety-critical calculations have exhaustive branch or property-based test coverage.
10. Concurrency and idempotency scenarios are covered for shared-state or distributed-write operations.
11. Experiments verify exposure logging, assignment stability, SRM detection, metric queries, and guardrail rollback.
12. ML model rollouts verify model version, feature store correctness, drift/fairness metrics, online/offline metric alignment, and rollback model.
13. Monorepo affected-test and cache policies are validated against module graph changes and a full-suite fallback.
14. Agent-reported test completion includes evidence inventory and does not rely on unsupported claims.
15. Non-trivial tests have names or comments that explain the protected behavior.
16. Regression tests mention the historical bug, failure mode, or invariant being protected.
17. Fixture/golden data explains the contract it represents.
18. Test comments explain scenario and purpose, not test framework mechanics.
19. Test files and helpers follow the owning module boundary or document the local convention.
20. Shared test utilities contain only pure technical helpers, not module-specific business fixtures.
21. Tests do not rely on private helper access when public behavior can prove the outcome.
22. Module splits include corresponding test and fixture ownership review.
23. Test pass claims map to the actual command and suite that ran; a lint or type-check pass is never reported as a test pass, and a single passing test is never reported as full-suite or full-coverage success.
24. Minimal checks are accepted only for risk levels where they actually prove the selected behavior; high-risk gates keep their required unit, integration, contract, security, reliability, migration, or rollback evidence.
25. Reused test results are fresh: if code or inputs changed after a run, the suite is re-run before the pass is claimed.
26. Test acceptance maps to the acceptance criteria and non-goals (spec compliance) before test-quality sign-off; a clean test suite does not substitute for a missing required behavior.
27. Every proposed or reported test states what it proves and what it does not prove.
28. Bug fixes include regression evidence for the verified defect or a documented reason the regression is non-automatable.
29. Private helpers are not exported only for tests; tests exercise public behavior or explicit seams.
30. Time, randomness, UUIDs, concurrency, and external I/O are deterministic or explicitly isolated in tests.
31. Failure contracts and model mappings have negative-path and compatibility coverage when they cross boundaries.

## Handoff
- **backend-change-builder** — with test obligations for service, repository, and API layers.
- **data-middleware-change-builder** — with migration test and query plan validation obligations.
- **frontend-change-builder** — with accessibility test, component behavioral test, and E2E flow obligations.
- **integration-change-builder** — with sandbox integration, idempotency, and failure simulation obligations.
- **delivery-release-gate** — when release evidence requires specific test results before deployment.
- **security-privacy-gate** — with security-specific test obligations for auth, input handling, and data access.
- **ai-product-extension** — with ML evaluation, drift, fairness, model registry, and rollback obligations.
- **bigdata-product-extension** — with analytics event, feature store, data quality, and warehouse validation obligations.
- **agent-execution-discipline** — when test evidence, route repair, or closure package is missing from an agent-assisted change.
- **testability-seam-design** — when public behavior boundary, deterministic seam, test double, fixture ownership, or private-helper non-export decisions are unresolved.
- **failure-contract-design** — when negative tests need typed boundary failure semantics.
- **model-boundary-mapping** — when DTO, domain, persistence, event, or view model mapping tests are required.
- **algorithm-data-structure-selection** — when scale-sensitive tests require complexity, memory, streaming, or benchmark evidence.
- **data-side-effect-flow-tracing** — when tests must prove transaction, cache, event, external IO, or hidden side-effect ordering.
- **consumer-impact-analysis** — when tests must prove old/new API, SDK, schema, event, export, or generated-client compatibility.
- **cleanup-deletion-governance** — when tests must prove deletion safety, caller search, telemetry, rollback, or stale-branch removal.
- **architecture-enforcement-tooling** — when test selection, import rules, generated-file policy, exports, or forbidden dependency checks need CI enforcement.

## Completion Criteria
The change has a proportional, executable verification plan where every material risk maps to test evidence or an explicitly accepted residual risk with justification — and the complete test strategy can be handed to a builder without ambiguity about what must pass before release.
