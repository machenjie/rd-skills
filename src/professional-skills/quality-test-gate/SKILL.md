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

## Stage Ownership
Own the TDD slice for ChangeForge process traces: PDD acceptance-to-test mapping, DDD invariant-to-test or code mapping, SDD public API-to-test mapping, failure-mode tests, logging/security tests, and validation commands. When logging is required, verify `logging-design-gate` fields, redaction, denial, retry, fallback, and trace propagation evidence.

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
- **Changed code maps to tests**: every material changed branch, public contract, migration, fixture, generated artifact, or integration seam must map to a specific test, validation command, or explicitly accepted residual risk.
- **Validation freshness is mandatory**: if source, fixtures, configs, generated inputs, lockfiles, migrations, or test data change after a validation run, the affected validation is stale and must be re-run or reported as not verified.
- **Validation Broker results are closure inputs**: when a broker plan or result is available, use it to map changed paths and risk surfaces to narrow/module/full commands, inspect outcome and freshness, and treat stale, failed, not-run, no-outcome, or coverage-mismatch results as incomplete validation. Broker recommendations do not execute commands automatically and do not replace professional judgment.
- **Broker owns freshness classification**: use `validation-broker` as the source for changed-path-to-validation mapping, validator depth, parsed outcomes, freshness, negative validation evidence, and stop-closure validation status.
- **Flaky tests need classification**: a flaky, retried, quarantined, or skipped test must be classified by signature, owner, affected risk, quarantine/remediation path, and why its missing signal does or does not block the change.
- **Minimal validation is risk-bound**: L1 low-risk changes may use the smallest meaningful runnable check, but a smoke check is not evidence for money, security, auth, data migration, retry/idempotency, or production reliability correctness. Do not delete a meaningful smoke or self-check as bloat.
- **Test structure follows module structure**: test files, fixtures, factories, mocks, and golden data must have an owning module or contract boundary; shared test helpers must not become business-fixture dumping grounds.
- **Tests exercise public behavior by default**: refactors and splits are verified through public APIs, module contracts, or observable behavior, not private helper calls that freeze implementation details.
- **Assertions must be mutation-resistant enough for the risk**: tests for material behavior must fail when the implementation branch, permission check, mapping, calculation, side effect, or failure contract is removed or inverted; shallow existence and call-count assertions are not sufficient.
- **AI patch test debt is explicit**: generated or agent-assisted patches must list tests added, tests reused, tests intentionally not added, stale validations, and follow-up debt with an owner when full coverage is deferred.

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
- **Code element risk**: Do variables, expressions, or statements decide defaults, truthiness/nullish behavior, fallthrough, cleanup, loop mutation, broad try scope, or side-effect order? Requires focused tests, static analysis, or review proof for the named element behavior.

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
| Business golden case gate | Business rule, workflow, reason code, semantic review, or BSP validation changes. | Map business claims to executable golden cases, owner review, or explicit residual risk. | Rule/workflow claim, positive/negative golden case, validator command, source-backed FACT evidence. | `business-semantic-control-plane`, `validation-broker` | Technical green checks without business behavior cases. |

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
- **Signal:** changed code relies on null/default sentinels, truthiness, mixed precedence, switch fallthrough, loop-counter mutation, broad try/catch scope, mutable default values, hidden assignment, or cleanup statements without a targeted assertion. **Hidden risk:** tests can pass happy paths while the local element fails edge cases. **Required professional action:** add or identify a focused element-level regression. **Route to:** `code-element-professionalism`, `regression-testing`, `language-testing-strategy`. **Evidence required:** edge-case fixture, assertion that would fail on the element defect, and command output or not-run disclosure.
- **Signal:** public API, SDK, schema, event, or export change lacks old/new consumer compatibility tests. **Hidden risk:** local tests pass while downstream consumers break. **Required professional action:** add consumer impact and contract evidence. **Route to:** `consumer-impact-analysis`, `contract-testing`. **Evidence required:** consumer inventory, compatibility cases, generated-client check, migration/deprecation note, and telemetry plan.
- **Signal:** cleanup deletes flags, fallbacks, deprecated APIs, compatibility branches, or dead code without caller-search and rollback tests. **Hidden risk:** deletion removes runtime or generated references that ordinary unit tests miss. **Required professional action:** test cleanup/deletion governance before closure. **Route to:** `cleanup-deletion-governance`, `regression-testing`. **Evidence required:** caller search, telemetry or retained-risk decision, removed/preserved behavior tests, and rollback path.
- **Signal:** test confidence depends on import boundaries, generated-file policy, public/private exports, affected-test rules, or forbidden dependencies that are not enforced in CI. **Hidden risk:** missing CI enforcement lets tests be skipped or wrong architecture violations merge unnoticed. **Required professional action:** require architecture enforcement evidence or mark the test gate incomplete. **Route to:** `architecture-enforcement-tooling`, `ci-cd`. **Evidence required:** rule list, CI command, representative failure, generated-code exception, and affected-test proof.
- **Signal:** test plan lacks negative case for permission, idempotency, concurrency, invalid input, or partial failure. **Hidden risk:** missing negative-path regression leaves happy-path confidence only. **Required professional action:** add a mutation-like negative case for the named risk. **Route to:** `backend-change-builder`, `security-privacy-gate`, `data-middleware-change-builder`. **Evidence required:** denied/invalid/retry/partial-failure test output and what evidence proves.
- **Signal:** changed files, branches, fixtures, or generated inputs are not mapped to test obligations, or validation evidence predates the final edit. **Hidden risk:** handoff reports green evidence for code that was never exercised. **Required professional action:** build a changed-code-to-test map and re-run stale checks. **Route to:** `plan-execution-consistency`, `regression-testing`. **Evidence required:** changed path, covered behavior, command, outcome, stale/not-run disclosure, and residual risk owner.
- **Signal:** assertions only check existence, snapshot shape, mock calls, or private helper internals. **Hidden risk:** hidden wrong branch, permission check, mapping, or failure contract survives because the test has no behavior-sensitive assertion. **Required professional action:** require public-behavior proof and verify mutation-style assertion quality for the named risk. **Route to:** `testability-seam-design`, `code-clarity-maintainability`. **Evidence required:** behavior boundary map, mutation or inversion test output that would fail, rejected private-helper assertion, and residual assertion-debt owner.

### Decision Tree: Test Depth Required

Use the smallest evidence level that can fail for the named risk. Financial, authorization, safety, migration, public contract, external integration, auth/session, experiment, ML, and affected-test/cache changes require their specific negative, rollback, contract, sandbox, guardrail, model, or full-suite validation. Low-risk refactors may reuse existing tests only when coverage and behavior are unchanged.

Load `references/test-output-and-gates.md` for the full test-depth decision tree and exhaustive output/gate contract.

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
- Escalate to `code-element-professionalism` when test evidence must prove low-level variable, expression, statement, cleanup, fallthrough, or default semantics.

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
Return a test strategy with actionable evidence:
- **Mode selected:** new behavior, bug-fix regression, contract/migration, integration, frontend/a11y, flaky/performance/security, or minimal validation, with trigger.
- **Boundaries inspected:** changed code paths, public contracts, fixtures, mocks, generated files, DB/cache/queue/provider seams, UI states, CI selection, and release boundaries.
- **Risk-to-test mapping:** each material risk paired with required test type, depth, pass criteria, and why cheaper or heavier evidence is insufficient.
- **Changed-code-to-test map:** every material changed path, branch, public contract, fixture, generated input, and integration seam mapped to tests/validators or residual risk.
- **Validation broker result:** narrow/module/full validator choice, freshness, stale or unrun commands, negative evidence, and stop-closure consequence.
- **Business golden cases:** BSP claim-to-test map, rule/workflow/reason-code coverage, owner review, not-run status, and residual semantic risk when business semantics are selected.
- **Structure and seam plan:** fixture/factory/mock/golden ownership, public-behavior boundary, fake/stub/mock/spy decision, deterministic inputs, and private-helper non-export decision.
- **Validation evidence:** commands, exit codes, artifacts, what evidence proves, what evidence does not prove, validation freshness, and evidence limits.
- **Residual risk and next gate:** accepted gaps, flaky classifications, manual evidence, owner, and next gate or no-next-gate rationale.

## Business Golden Case Gate

When BSP is selected, every changed business rule, workflow transition, permission or denial reason code, and negative path must map to at least one of:

- business golden case or tabular rule case with stable rule/workflow id
- executable test covering the changed path and one denied/forbidden path
- owner review with current source or validation reference
- explicit residual risk with owner and release consequence

Green generic tests do not prove a changed business semantic claim unless the test names the rule/workflow/reason code or is mapped in the BSP `validation_map`.
A missing business golden case for a changed rule, workflow, permission, or reason code is a test-gate risk. Each changed rule/workflow/permission reason code must map to a test, owner review, or explicit residual risk before closure.

## Evidence Contract
Close a test strategy only when the canonical answers from `agent-execution-discipline` are concrete:
- **Basis:** selected mode, risk-to-test map, and why that depth fits the risk.
- **Files and boundaries inspected:** code paths, public contracts, fixtures, mocks, generated files, integration seams, UI states, CI selection, release boundaries, and mock-versus-real choices.
- **Reuse / placement rationale:** why each test, fixture, factory, mock, golden file, or helper sits at its selected unit/integration/contract/E2E/migration owner boundary.
- **Validation evidence:** literal suites/validators, exit code, obligation satisfied, what evidence proves, and what evidence does not prove.
- **Testing judgment, residual risk, and next gate:** changed-code-to-test mapping, validation freshness, assertion quality, behavior preservation, coverage gaps, flaky limits, owner, and handoff.

## Quality Gate
- Every material risk maps to a test/validator or explicit accepted residual risk with pass/fail criteria.
- Negative paths, authorization denied cases, failure contracts, model mappings, concurrency, idempotency, and rollback are covered when relevant.
- Migration, contract, integration, security, reliability, experiment, ML, monorepo affected-test, and cache evidence use the required depth for their risk.
- Mock assumptions are validated; private helpers are not exported only for tests; tests exercise public behavior or explicit seams.
- Code element risks have focused assertions or accepted residual risk for default/nullish, truthiness, precedence, fallthrough, loop, cleanup, and side-effect-order behavior.
- Test data contains no production PII; fixtures, golden data, helpers, and comments have owners and explain protected behavior.
- Flaky, skipped, retried, or quarantined tests have signature, owner, risk classification, and remediation path.
- Validation evidence is fresh against final source, configs, fixtures, generated inputs, migrations, and lockfiles.
- Partial validation is reported honestly; lint/typecheck/single-test passes are not presented as full-suite or full-coverage success.
- Business semantic rules, workflows, reason codes, and owner decisions map to golden cases, owner review, or explicit residual risk; graph and memory do not prove business behavior alone.
- New or changed BSP validation_map entries with status `mapped` include non-memory evidence; memory-only or graph-only mappings block closure.

## Handoff
- Hand service/API test obligations to `backend-change-builder`; data/query/migration obligations to `data-middleware-change-builder`; UI/a11y obligations to `frontend-change-builder`; integration/idempotency/failure simulation to `integration-change-builder`.
- Hand release-blocking evidence to `delivery-release-gate`; auth/input/data-access tests to `security-privacy-gate`; ML or analytics validation to `ai-product-extension` or `bigdata-product-extension`.
- Hand unresolved seams, failure contracts, model mappings, algorithm scale, side-effect ordering, consumer compatibility, cleanup deletion, or architecture enforcement to the matching capability owner.
- Hand variable, expression, statement, default, fallthrough, cleanup, and local side-effect-order proof gaps to `code-element-professionalism`.
- Hand missing evidence, route repair, validation freshness, or closure-package gaps to `agent-execution-discipline`.

## Completion Criteria
The change has a proportional, executable verification plan where every material risk maps to test evidence or an explicitly accepted residual risk with justification — and the complete test strategy can be handed to a builder without ambiguity about what must pass before release.
