# Test Output And Gates

Load this reference when `quality-test-gate` needs the full test-depth decision tree, exhaustive output fields, quality gates, or handoff routing table. The skill body keeps the default runtime context compact.

## Test Depth Decision Tree

```
Does the change modify a financial calculation, authorization decision, or safety-critical rule?
├── Yes -> Unit tests for ALL branches + failure cases + property-based or mutation test required
Does the change modify a database schema or data migration?
├── Yes -> Migration test (forward + rollback) + data integrity check required
Does the change modify a public API or event schema with known consumers?
├── Yes -> Consumer-driven contract tests (Pact) required
Does the change involve an external integration (payment, identity, third-party API)?
├── Yes -> Sandbox integration tests + failure simulation required
Does the change touch auth, session, or permission boundaries?
├── Yes -> Security-specific test cases: boundary values, privilege escalation, session fixation
Does the change add or modify an A/B test or analytics metric?
├── Yes -> Exposure logging test + assignment stability + SRM check + guardrail rollback test
Does the change roll out an ML model?
├── Yes -> Offline eval + shadow/canary + drift/fairness checks + rollback model version test
Does the change use monorepo affected tests or build cache?
├── Yes -> Module graph validation + cache key verification + generated file policy + full-suite fallback
Is the change a low-risk refactoring with no behavior change?
└── Run existing test suite; no new tests required if coverage is not reduced
```

## Output Contract
Return a test strategy with:
- **Mode selected**: new behavior, bug-fix regression, contract/migration, integration, frontend/a11y, or flaky/performance/security, with trigger signal.
- **Boundaries inspected**: changed code paths, branches, public contracts, fixtures, mocks, generated files, DB/cache/queue/provider seams, UI states, CI selection, and release boundaries inspected or skipped with reason.
- **Professional judgment**: test depth decision, risk accepted or ruled out, and why cheaper or heavier evidence is insufficient or unnecessary.
- **Risk-to-test mapping**: Each identified risk paired with its required test type, depth, and pass criteria.
- **Changed-code-to-test map**: every material changed path, branch, public contract, fixture, generated input, and integration seam paired with covering tests/validators or residual risk.
- **Changed-path validation map**: narrow/module/full validator selection, unvalidated changed paths, stale commands, and stop-closure consequence from `validation-broker`.
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
- **Validation freshness**: source/config/fixture/generated inputs covered by each validation, last material edit after the run, stale checks re-run, and checks intentionally not re-run.
- **Validation broker result**: changed paths/risk surfaces considered, recommended command level used, outcome, freshness after final material edit, coverage alignment, and why any full validator was skipped.
- **Assertion quality review**: public behavior boundary, mutation-style failure expectation, private-helper rejection, shallow assertion debt, and mock-call-only findings.
- **Flaky classification**: flaky or skipped tests, signature, owner, quarantine/remediation path, blocked risk, and accepted residual risk.
- **Evidence limits**: what each test proves and what it does not prove about integration seams, scale, browsers, production data, flake risk, or release readiness.
- **Residual risks**: Accepted gaps with explicit business justification and mitigating controls.
- **Next gate/handoff**: implementation, contract, security, reliability, release, or no-next-gate rationale.

## Evidence Contract
Close a test strategy only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: the selected mode, risk-to-test mapping each test layer rests on, and why that layer is the right depth for the risk.
- **Files and boundaries inspected**: code paths, branches, public contracts, fixtures, mocks, generated files, integration seams, UI states, CI selection, and release boundaries the strategy covers, and the mock-versus-real boundary chosen for each dependency.
- **Placement rationale**: why each test sits at its level (unit/integration/contract/E2E/migration) instead of a cheaper or more expensive one.
- **Validation commands**: the literal test suites and validators run, each with its exit code, the obligation it satisfies, what evidence proves, and what evidence does not prove.
- **Testing judgment and handoff**: mode selected, changed-code-to-test mapping, risk-to-test judgment, validation freshness, assertion quality, behavior preservation when applicable, evidence limits, and next gate.
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
24. Negative validation evidence from the broker is preserved and not hidden behind later unrelated passes.
25. Minimal checks are accepted only for risk levels where they actually prove the selected behavior; high-risk gates keep their required unit, integration, contract, security, reliability, migration, or rollback evidence.
26. Reused test results are fresh: if code or inputs changed after a run, the suite is re-run before the pass is claimed.
27. Test acceptance maps to the acceptance criteria and non-goals before test-quality sign-off; a clean test suite does not substitute for a missing required behavior.
28. Every proposed or reported test states what it proves and what it does not prove.
29. Bug fixes include regression evidence for the verified defect or a documented reason the regression is non-automatable.
30. Private helpers are not exported only for tests; tests exercise public behavior or explicit seams.
31. Time, randomness, UUIDs, concurrency, and external I/O are deterministic or explicitly isolated in tests.
32. Failure contracts and model mappings have negative-path and compatibility coverage when they cross boundaries.
33. Every material changed code path, fixture, generated artifact, or public contract maps to a test/validator or an explicit residual risk.
34. Validation evidence is fresh against the final changed files, configs, fixtures, generated inputs, and lockfiles.
35. Material assertions would fail on an inverted, removed, or bypassed implementation branch; shallow existence, snapshot, mock-call, and private-helper assertions are flagged.
36. Flaky, skipped, retried, or quarantined tests have a signature, owner, risk classification, and remediation path.
37. Agent-assisted patches list test debt and not-run obligations explicitly; missing tests cannot be hidden behind a clean partial run.

## Handoff
- **backend-change-builder**: test obligations for service, repository, and API layers.
- **data-middleware-change-builder**: migration test and query plan validation obligations.
- **frontend-change-builder**: accessibility test, component behavioral test, and E2E flow obligations.
- **integration-change-builder**: sandbox integration, idempotency, and failure simulation obligations.
- **delivery-release-gate**: release evidence requires specific test results before deployment.
- **security-privacy-gate**: security-specific test obligations for auth, input handling, and data access.
- **ai-product-extension**: ML evaluation, drift, fairness, model registry, and rollback obligations.
- **bigdata-product-extension**: analytics event, feature store, data quality, and warehouse validation obligations.
- **agent-execution-discipline**: test evidence, route repair, or closure package is missing.
- **testability-seam-design**: public behavior boundary, deterministic seam, test double, fixture ownership, or private-helper non-export decisions are unresolved.
- **failure-contract-design**: negative tests need typed boundary failure semantics.
- **model-boundary-mapping**: DTO, domain, persistence, event, or view model mapping tests are required.
- **algorithm-data-structure-selection**: scale-sensitive tests require complexity, memory, streaming, or benchmark evidence.
- **data-side-effect-flow-tracing**: tests must prove transaction, cache, event, external IO, or hidden side-effect ordering.
- **consumer-impact-analysis**: tests must prove old/new API, SDK, schema, event, export, or generated-client compatibility.
- **cleanup-deletion-governance**: tests must prove deletion safety, caller search, telemetry, rollback, or stale-branch removal.
- **architecture-enforcement-tooling**: test selection, import rules, generated-file policy, exports, or forbidden dependency checks need CI enforcement.
