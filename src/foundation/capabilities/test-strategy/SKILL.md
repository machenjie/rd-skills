---
name: test-strategy
description: Selects risk-based verification levels by change type, impact area, and production risk, with layered tests required for high-risk changes.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "58"
changeforge_version: 0.1.0
---

# Mission

**Select a risk-proportionate verification strategy that specifies the minimum sufficient set of test levels, test cases, and evidence required to prove a change is correct and production-safe** — without wasting engineering time on low-risk coverage that adds cost without adding confidence, and without omitting high-risk coverage that leaves production vulnerabilities undiscovered until after deployment.

# When To Use

Use this capability when: a change requires verification planning and the appropriate test levels are not obvious from the change type alone; the change introduces a new user journey, API endpoint, database schema migration, authentication mechanism, external integration, or behavioral regression risk; a change is flagged as high-risk (security, payments, data migration, public API contract, multi-tenant isolation) and layered verification must be specified; the previous test coverage for a changed area is unknown or incomplete; or an omission of a test level must be formally justified with residual risk documentation.

# Do Not Use When

Do not use this capability for: selecting test tooling or writing the tests themselves (use `unit-testing`, `integration-testing`, `contract-testing`, `e2e-testing`); test data management beyond the strategy selection (use `test-data-management`); post-deployment observability monitoring (use `observability-design`); changes so trivial that the test level is self-evident (typo fix in a static string with no behavior change — unit test only, zero planning required).

# Non-Negotiable Rules

- **Select test levels based on change type, impact area, risk level, and failure consequence — not based on team habit or test framework availability.** "We always write E2E tests" is not a test strategy. "This is an auth flow change with multi-tenant isolation implications; it requires unit tests for guard logic, integration tests for session behavior, and a security permission matrix test for tenant isolation" is a test strategy.
- **High-risk changes require layered verification across multiple test levels.** A change that affects authentication, payment, data migration, or a public API contract cannot be verified by a single test level. Layering means: unit tests prove local rules; integration tests prove real boundary behavior; contract tests protect consumers of changed interfaces; E2E tests prove critical user journey completion; regression tests lock previously defective paths. All layers must be specified with the specific behaviors each level is responsible for proving.
- **Prefer fast, deterministic tests for local business rule logic.** A complex validation algorithm, a price calculation formula, a business rule guard — these should be proven at the unit level with a rich matrix of cases. Moving these to E2E tests means: 100× slower feedback, external dependencies that can fail for unrelated reasons, and test debt that grows with every new business rule case. The testing pyramid principle: most tests at the unit level, progressively fewer at higher levels.
- **Negative, permission, rollback, migration, and failure paths must be tested when those paths are exercised by the change.** A test strategy that has only happy-path cases for a payment flow is incomplete — it does not prove that a payment failure is handled, that an unauthorized user is rejected, that a partial migration can be rolled back, or that a third-party timeout is recovered. If these paths are NOT tested, that must be an explicit documented decision with residual risk and compensating evidence, not an oversight.
- **Omitted test levels require explicit justification: technical reason, residual risk, and compensating evidence.** "We don't have time" is not a technical reason. Acceptable technical reasons: "the test level is covered by a separate gate (security-privacy-gate performs a dedicated auth matrix review)"; "the behavior is stateless and entirely covered by unit tests with 100% branch coverage"; "the external dependency has an SLA test in the provider's own suite (contract test by provider)." Residual risk must be rated. Compensating evidence must be named.
- **Test evidence must trace to acceptance standards and changed behavior.** Each test must answer: "which acceptance criterion does this prove?" and "which changed behavior does this exercise?" A test that cannot be traced to an acceptance criterion or a changed code path is a test that proves nothing about correctness — it is coverage theater.

# Industry Benchmarks

Anchor against: **Kent Beck — Testing Pyramid** (unit → service → UI in 70/20/10 proportion; cheap fast feedback at the bottom, expensive slow confirmation at the top). **Martin Fowler / Guillermo Rauch — Testing Trophy** (static analysis, unit, integration, E2E in 0/40/40/20 proportion; emphasizes integration tests for the boundary layer). **Google Testing Blog — "Just Say No to More End-to-End Tests"** (E2E as final confirmation, not primary coverage mechanism). **DORA Research** — test automation maturity correlates with low change failure rate, high deployment frequency, and fast mean time to restore. **OWASP ASVS (Application Security Verification Standard)** — test requirements for authentication (L1/L2/L3), session management, access control, input validation, cryptography, API security. **ISO/IEC 25010 — Quality Characteristics** — functional correctness, reliability, performance efficiency, security, compatibility — each quality characteristic maps to specific test levels. **ISTQB Test Design Techniques** — equivalence partitioning, boundary value analysis, decision table testing, state transition testing — systematically deriving test cases from specifications. **Contract Testing — Pact (Consumer-Driven Contract Testing)** — consumer verifies provider contract without needing provider running; prevents silent API contract breakage across services.

### Risk-Based Test Level Selection Matrix

| Change Type | Unit | Integration | Contract | E2E | Migration | Performance | Security |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bug fix (local logic) | **Required** | If boundary affected | If interface changed | Regression test only | No | No | If security bug |
| New business rule | **Required** (full case matrix) | If DB/API affected | If API exposed | Journey test if user-facing | No | If high-volume | If permission rule |
| Database schema migration | Migration script test | **Required** | No | Regression after migration | No | If large table | If PII affected |
| API contract change | **Required** (new behavior) | **Required** | **Required** | If public-facing | No | If SLA change | OWASP API test |
| Authentication/auth flow | Unit (guard logic) | **Required** | No | **Required** (permission matrix) | No | Session load | **Required** (OWASP ASVS L2) |
| Payment flow | Unit (calculation) | **Required** | Provider contract | **Required** (happy + failure) | No | Transaction load | PCI-DSS controls |
| External integration | Unit (mock) | **Required** (real adapter) | **Required** | Happy path only | No | Timeout/retry | API key rotation |
| Refactor (no behavior change) | **Required** (regression) | If boundary changed | No | Smoke test only | No | No | No |
| Performance optimization | No behavior tests | Load test | No | Smoke test | No | **Required** (before/after benchmark) | No |

### Testing Level Trade-off Table

| Test Level | Speed | Isolation | Cost | What It Proves |
| --- | --- | --- | --- | --- |
| Unit | < 1ms per test | Full (mocked deps) | Low | Local logic correctness; edge cases; error paths |
| Integration | 10ms–5s per test | Partial (real DB/cache/broker) | Medium | Boundary behavior; DB queries; adapter contracts |
| Contract (Pact) | < 100ms per test | Full (recorded stubs) | Medium | API contract compatibility across service versions |
| E2E | 2s–60s per test | None (real system) | High | User journey completion; cross-service orchestration |
| Migration | Minutes | Full (migration + schema check) | Medium | Schema changes are backward-compatible; rollback succeeds |
| Performance | Minutes | None (real load) | High | Throughput, latency, error rate under load |
| Security (DAST) | Minutes–hours | Partial | High | OWASP Top 10 vulnerabilities in running application |

### Omission Justification Template

```yaml
test_level_omitted: "contract-testing"
change: "Internal BFF → Microservice call (not public API)"
technical_reason: >
  Contract is owned by the same team; the consumer (BFF) and provider (service)
  are deployed together in a monorepo CI pipeline. The integration test suite
  exercises the real interface on every build, providing equivalent coverage.
residual_risk: "Low — single ownership; no external consumer."
compensating_evidence: "Integration test T-042 exercises the full request-response contract."
sign_off: "tech-lead@team.example.com"
```

# Selection Rules

Select this capability when **the appropriate verification levels for a change are not self-evident and risk-based selection is needed**. Route to individual test capabilities for level-specific design: `unit-testing`, `integration-testing`, `contract-testing`, `e2e-testing`, `regression-testing`, `performance-budgeting`, `backup-recovery`. Route to `security-privacy-gate` for security test requirements on auth/payment/PII changes. Route to `test-data-management` for fixture and isolation design once the strategy is confirmed.

# Risk Escalation Rules

Escalate when: the change affects authentication, payments, multi-tenant isolation, or irreversible data operations and no integration or E2E tests are proposed (high risk release without adequate verification — must block); a test level is omitted for a high-risk change with no documented compensating evidence (hidden release risk — must require justification); the previous test coverage for a changed area is zero and the change is not a pure refactor (coverage debt with behavioral risk — must add baseline tests); or E2E tests are the only proposed coverage for complex business rule logic (slow, fragile coverage — must add unit-level tests).

# Critical Details

- **Code coverage percentage is not a test strategy and must not be cited as evidence of safety.** 80% line coverage can include 0% of the failure paths, 0% of the permission matrix, and 0% of the rollback paths. Coverage metrics are a useful development-time feedback signal, not a release gate. The question is not "what percentage of lines are covered?" but "which behaviors, risks, and paths are proven by specific named tests?"
- **The most dangerous test strategy gap: no negative test cases for high-risk operations.** A payment flow with only happy-path tests proves the payment succeeds when everything works — it does not prove the payment fails safely when the gateway is down, the card is declined, the amount is negative, or the idempotency key is replayed. Negative cases are not "extra" — they are the evidence that the system behaves correctly under the conditions most likely to cause financial loss or data corruption.
- **E2E tests are confirmation, not coverage.** An E2E test that proves a login flow works does not prove that SQL injection in the username field is rejected, that a session token is invalidated after logout, or that concurrent logins from different devices are handled correctly. E2E tests confirm that the system works end-to-end in the happy path — the detailed security, edge case, and error handling coverage must be at lower, faster test levels.
- **Migration tests must be run against a schema snapshot of production, not against a clean database.** A migration that passes on a fresh schema may fail on a production schema that has years of accumulated data, indexes, constraints, foreign keys, and partial migrations from previous releases. The migration test must run against a recent production schema dump (with data sanitized) to catch incompatibilities.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| "We have 85% code coverage" as release evidence | Coverage % includes no information about what behaviors are proven | Name specific tests and acceptance criteria they prove |
| Only E2E tests for a complex price calculation | E2E tests are 100× slower; calculation has 50 edge cases needing a matrix | Unit test matrix for calculation logic; E2E tests for checkout flow only |
| Auth flow change with no permission matrix test | Unauthorized users may gain access; privilege escalation not detected | OWASP ASVS L2 permission matrix: every role × every endpoint × expected result |
| Migration deployed with tests on clean schema only | Migration fails on production schema with FK constraint violation | Run migration test on sanitized production schema dump |
| Omitted negative tests: "happy path passes" | Payment failure path untested; gateway timeout causes hung order | Negative cases: card declined, gateway timeout, duplicate charge idempotency |
| Contract test skipped: "we own both services" | Silently breaking changes in API responses; consumer fails in production | Contract test verifies the response schema that the consumer actually depends on |

# Failure Modes

- Auth change with only unit tests: integration test would have caught session cookie not being set correctly.
- Payment flow with no failure path tests: gateway timeout causes double-charge that is only caught in production.
- Migration tested on clean schema: production migration fails on FK constraint; rollback required.
- E2E test suite is the only coverage: test run takes 45 minutes; flaky tests block every deployment.
- High-risk change released with undocumented test omissions: post-incident review reveals coverage gap was known.
- Contract breaking change silently deployed: consumer service starts returning 500; no contract test caught it.

# Output Contract

Return a test strategy with:

- `change_type` and `impact_areas` (surfaces, layers, integrations affected)
- `risk_rating` (low/medium/high/critical with rationale)
- `required_test_levels` (per level: specific behaviors each level proves, test cases, owner, acceptance criterion trace)
- `omitted_levels` (per omission: technical reason, residual risk rating, compensating evidence, sign-off)
- `negative_and_boundary_coverage` (which error paths, permission denials, migration rollbacks are tested)
- `regression_guardrails` (tests that must not regress; CI enforcement)
- `test_data_requirements` (fixtures, factories, isolation mechanism — delegate to `test-data-management`)
- `release_blocking_criteria` (which test results must be green before release is approved)
- `evidence_artifacts` (test report locations, coverage reports, contract verification results)

# Quality Gate

The strategy is complete only when:

1. Risk rating is justified with change type and failure consequence.
2. Every selected test level names the specific behaviors it proves.
3. Every test level maps to an acceptance criterion or changed behavior.
4. All high-risk paths (negative, permission, rollback, migration) are explicitly addressed.
5. All omitted test levels have technical reason, residual risk, and compensating evidence.
6. E2E tests are not the only coverage for complex logic that belongs at lower levels.
7. Migration tests are specified to run against a production schema snapshot.
8. Release-blocking criteria are named and enforceable in CI.
9. OWASP ASVS requirements are cited for auth/security changes.
10. DORA batch size guidance is considered (small changes require less verification overhead).

# Used By

- quality-test-gate
- task-dag-planner

# Handoff

Hand off to `unit-testing` for local logic verification; `integration-testing` for boundary behavior; `contract-testing` for API interface compatibility; `e2e-testing` for user journey confirmation; `regression-testing` for locking defect-fix behavior; `performance-budgeting` for load and latency verification; `backup-recovery` for migration and data integrity drills; `test-data-management` for fixture and isolation design.

# Completion Criteria

The capability is complete when **verification depth is proportionate to risk, high-risk changes have layered evidence across multiple test levels, all omissions are formally justified, and every test traces to an acceptance criterion or a changed behavior**.
