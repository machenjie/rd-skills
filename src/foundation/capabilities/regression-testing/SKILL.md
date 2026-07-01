---
name: regression-testing
description: Requires bug fixes and risky changes to add regression coverage that reproduces the failure and prevents recurrence unless impossible and documented.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "64"
changeforge_version: 0.1.0
---

# Mission

**Add automated test coverage that reproduces a specific past failure, prevents that failure from recurring, and anchors it to the defect or incident that caused it** — so that future code changes are proven safe against the known failure surface, and reviewers can verify regression coverage is present before a fix is merged.

# When To Use

Use this capability when: a bug is confirmed and a fix is being prepared — the regression test must reproduce the failure before the fix and pass after the fix; a production incident is resolved and residual risk of recurrence is unacceptable; a code review or QA review flags a defect and regression prevention is a gate criterion; a refactoring touches a code path that has had prior defects (historical failure zones); or a security finding is remediated and a non-regression test is required as evidence (e.g., OWASP Testing Guide requirement for fixed vulnerabilities).

# Do Not Use When

Do not use this capability to: write general happy-path tests unrelated to a specific defect (those belong in `test-strategy`); write load or performance tests (use `performance-budgeting`); write contract tests (use `api-contract-design`); or duplicate tests that already reproduce the defect and are present in the test suite (verify coverage first before adding).

# Stage Fit

Use during bug-fix, testing, code-review, refactoring, and final validation. Per-stage focus:

- **bug-fix**: a test that reproduces the defect before the fix and passes after it; same-pattern coverage.
- **testing**: protect existing behavior while adding new coverage.
- **refactoring**: characterization tests that prove behavior was preserved.

# Non-Negotiable Rules

- **Every confirmed defect must have a regression test unless technically impossible, and impossibility must be documented.** "Technically impossible" means: the defect is in a non-deterministic timing or concurrency condition that cannot be reliably reproduced in a test; the defect requires hardware state that cannot be emulated; or the test infrastructure cannot simulate the required condition. Impossibility must be documented with: defect ID/reference, specific reason reproduction is infeasible, residual risk rating, and compensating control (monitoring, alerting, manual test script, chaos experiment). "We didn't have time" is not a valid impossibility reason.
- **The regression test must reproduce the original failure, not just test adjacent behavior.** A test that passes before the fix is a regression test. A test that was already passing before the fix is not a regression test — it is a confirmation test. The review discipline: run the test against the code before the fix was applied; it must fail for the right reason. The canonical formulation: "Red without fix, Green with fix" — also called a "failing test first" or red-green cycle for defects.
- **Use the narrowest test level that would have caught the defect.** If a unit test would have caught the defect, write a unit test — not an E2E test. Pyramid: Unit > Integration > E2E. Reasons: E2E tests are slower, flakier, and harder to maintain; a unit-level regression test provides faster feedback and clearer failure attribution. Decision: Could the defect be reproduced by calling a single function with the right input? → Unit test. Does the defect require real database state or external service interaction? → Integration test. Does the defect require a specific browser or UI rendering? → E2E test (as a last resort).
- **The regression test must capture the exact triggering conditions: input, state, role, timing, and dependency.** A regression test that uses a different input than the one that triggered the bug may pass even when the bug is reintroduced with the original input. Triggering conditions to capture: (1) the exact input value or payload; (2) the precondition state (user role, database state, feature flag, session state); (3) any timing or sequence dependency (e.g., the bug only occurs on the second API call, not the first); (4) the external dependency state (e.g., third-party API returns a specific error code). Use fixtures that mirror production data patterns.
- **Link every regression test to its defect, incident, or review finding.** This is not bureaucracy — it is the only way to answer "why does this test exist?" when someone encounters it in 18 months. The standard is: a comment or docstring on the test with the defect ID, incident reference, or PR/review link. Format: `// Regression: [BUG-1234] - Payment total rounds incorrectly for USD amounts with 3 decimal places`. Without this link, the test is an orphaned assertion that will be deleted in the next cleanup.
- **Untestable defects must be documented with residual risk and compensating evidence.** If a defect cannot be regression-tested, the engineering record must include: the defect reference, the fix description, why automated regression testing is not feasible, the residual risk level (how likely is recurrence and what is the impact if it recurs?), and the compensating control (production monitoring alert, chaos experiment, manual regression checklist item). This documentation satisfies audit and quality review requirements even without a test.

# Industry Benchmarks

Anchor against TDD red-green repair discipline, Feathers-style characterization tests for legacy change, test-pyramid level selection, OWASP non-regression evidence for fixed vulnerabilities, traceability standards for regulated work, DORA change-failure reduction, and mutation testing that proves the guard fails when the defect is reintroduced. Keep detailed templates in [references/checklist.md](references/checklist.md), source-to-evidence closure in [references/evidence-patterns.md](references/evidence-patterns.md), and regression benchmark patterns in [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) so the loaded body stays focused on routing, evidence, and gates.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Bug-fix regression | Confirmed defect, failing user scenario, incident, QA finding, or exploit fix. | Prove the exact recurrence path is red before fix and green after. | Defect reference, trigger input/state, pre-fix failure, post-fix command. | `quality-test-gate`, `failure-diagnosis` | Generic happy-path tests. |
| Security regression | IDOR, auth bypass, injection, XSS, CSRF, SSRF, secret leak, or permission bug. | Preserve the abuse case and denied behavior without unsafe live attack side effects. | Attack vector, denied-case test, same-pattern scan, security review note. | `security-privacy-gate`, `permission-boundary-modeling` | Absence-only authorization checks. |
| Refactor characterization | Risky cleanup, extraction, compatibility branch removal, or historical defect zone. | Lock existing observable behavior before structure changes. | Characterization cases, current behavior command, changed-path map. | `refactoring`, `code-review`, `validation-broker` | Testing private helpers. |
| Hard-to-reproduce defect | Flaky race, timing, hardware, external provider, production-only data, or disputed repro. | Choose deterministic replay, synthetic fixture, monitoring, or documented impossibility. | Feasibility decision, residual risk, compensating control, owner. | `testability-seam-design`, `observability`, `test-data-management` | Flaky CI test as proof. |
| Existing evidence reuse | Repository graph, project memory, prior red/green run, bug tracker, or old test report says covered. | Confirm current source, tests, fixtures, generated inputs, and validation freshness. | Inspected paths, accepted/rejected memory, command exit code, stale limits. | `repository-graph-analysis`, `project-memory-governance`, `plan-execution-consistency` | Stale green output as closure. |

# Proactive Professional Triggers

- **Signal:** a fix lands with no test that was observed failing before the fix. **Hidden risk:** the new test may describe correct behavior but never reproduce the defect. **Required professional action:** require red-before-fix evidence or document why it cannot be produced. **Route to:** `quality-test-gate`, `agent-execution-discipline`. **Evidence required:** command, commit/branch state, failure output, and matching-failure rationale.
- **Signal:** defect report includes exact input, role, tenant, state, feature flag, provider response, or timing sequence but the proposed fixture simplifies it. **Hidden risk:** recurrence path remains uncovered while a weaker test passes. **Required professional action:** capture the original trigger or a justified minimized equivalent. **Route to:** `test-data-management`, `unit-testing`, `integration-testing`. **Evidence required:** trigger map, fixture owner, equivalence rationale, and green-after-fix command.
- **Signal:** security, permission, data exposure, or injection bug is fixed without attack-vector regression coverage. **Hidden risk:** surrounding code can reintroduce the vulnerability under the same abuse path. **Required professional action:** add denied/abuse test and same-pattern scan without hitting live systems. **Route to:** `security-privacy-gate`, `permission-boundary-modeling`, `web-security`. **Evidence required:** malicious/denied test output, scanned paths, and residual untested vectors.
- **Signal:** race, flake, external dependency, hardware, production-only data, or performance-sensitive defect is labeled untestable. **Hidden risk:** "untestable" hides missing determinism work or lack of compensating controls. **Required professional action:** evaluate replay/fake/stub/contract/chaos/monitoring options and record residual risk. **Route to:** `testability-seam-design`, `observability`, `reliability-observability-gate`. **Evidence required:** infeasibility reason, rejected test options, alert/manual/chaos control, owner, and expiry.
- **Signal:** repository graph, project memory, bug tracker, old CI output, or previous agent report says regression coverage exists. **Hidden risk:** stale tests, changed fixtures, renamed paths, or final edits invalidate the claim. **Required professional action:** confirm current source and validation freshness before closure. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `validation-broker`. **Evidence required:** inspected files, accepted/rejected prior claim, fresh command/report path, and evidence limits.

# Selection Rules

Select this capability when a **specific past failure must be prevented from recurring** and the primary output is a test that was red before the fix and green after. Route elsewhere when: the test need is general coverage of new functionality (use `test-strategy`); the test targets a performance threshold (use `performance-budgeting`); the test validates a contract between services (use `api-contract-design`); or the test is for exploratory or manual verification (use `quality-test-gate` for test planning).

# Risk Escalation Rules

Escalate when: a defect cannot be regression-tested and the residual risk is HIGH or CRITICAL (requires risk acceptance sign-off from engineering lead or product owner); a security vulnerability is fixed and a regression test would require simulating an attack vector that might trigger security tooling or production systems (requires security team review before test implementation); a production incident is resolved but the triggering condition cannot be reliably reproduced in lower environments (requires incident post-mortem to define compensating monitoring before closure); or regression test coverage for a defect requires E2E tests that create real financial transactions or legal records in test environments (requires compliance review).

# Critical Details

- **"Red before fix, Green after fix" is the only verification that a regression test is a regression test.** The most common mistake: writing a test that describes correct behavior, running it against the fixed code, seeing it pass, and declaring "regression test added." This test may also pass against the unfixed code — meaning it provides no regression protection. The discipline: apply the test to the pre-fix code (via `git stash`, branch checkout, or revert), confirm it fails for the right reason, then verify it passes after the fix.
- **Flaky regression tests are worse than no regression tests.** A regression test that fails intermittently creates false alarms, erodes trust in the test suite, and is eventually disabled or deleted. Rule: if the test cannot pass consistently 100% of the time in CI, document it as a chaos experiment or monitoring alert instead.
- **Regression test fixtures must mirror production data patterns, not synthetic minimums.** A defect triggered by a 3-decimal-place USD amount should be tested with a 3-decimal-place amount. Over-simplified fixtures reduce test accuracy and create false confidence.
- **Security regression tests are the most critical category and most frequently skipped.** An authorization bypass, injection vulnerability, or authentication flaw that is fixed but not regression-tested will likely recur within 12 months as the surrounding code is modified. OWASP A01:2021, A03:2021, A07:2021 all require regression evidence in security reviews.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Test passes before fix AND after fix | Not a regression test; was already passing; provides no protection | Verify test is RED on pre-fix code; if not, it does not test the failure |
| Regression test uses `{ amount: 10 }` instead of production `{ amount: 10.005 }` | Simplified fixture does not reproduce the defect; false confidence | Use exact triggering input from defect report or production log |
| "No time for regression test" merged with fix | Defect recurs 6 months later with no automated detection | Block merge via PR gate: regression test required or documented-impossible |
| Regression test comment: `// test for payment bug` | No link to defect; orphaned in 12 months; deleted as "unclear purpose" | `// Regression: BUG-1234 — description — fixed in PR #567` |
| Flaky concurrency regression test added to CI | Intermittent failures; team learns to re-run until green; test disabled | Document as untestable; add monitoring alert + chaos experiment instead |
| E2E test for a bug catchable at unit level | Slow; fragile; expensive; hides simpler unit-level regression protection | Write unit test at narrowest level; add E2E only if UI interaction is essential |

# Failure Modes

- **Post-fix-only test** — passes on both versions; defect recurs; test is useless.
- **Oversimplified fixture** — does not reproduce exact triggering condition; original defect is not protected.
- **Skipped security regression** — authorization bypass is reintroduced during refactoring and discovered in penetration testing.
- **Missing defect link** — test is deleted during cleanup because its purpose is unclear; defect recurs.
- **Timing-sensitive CI test** — intermittent failures lead to disablement; defect recurs without signal.
- **Shared database integration test** — mutates shared data, breaks other tests, and is removed instead of repaired.
- **Stale coverage claim** — old CI output or project memory says the defect is covered, but current source, fixtures, or generated inputs changed after the run.
- **Over-broad regression suite** — an expensive E2E guard is added for a local rule; teams skip or quarantine it, so the recurrence path loses merge-gate protection.

# Reference Loading Policy

Load [references/checklist.md](references/checklist.md) when the defect is security-sensitive, concurrency-sensitive, production incident driven, difficult to reproduce, disputed in review, or when level selection / untestable documentation templates are needed. Load [references/evidence-patterns.md](references/evidence-patterns.md) only when closure depends on current repository graph, project memory, execution trajectory, red/green validation freshness, changed-defect-to-test mapping, tool permission boundaries, or residual-risk wording. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) only when selecting regression level, fixture fidelity, mutation/characterization strategy, hard-to-reproduce controls, or anti-pattern review. Use [examples/example-output.md](examples/example-output.md) when the required output shape is unclear. Do not load references for a simple deterministic bug when the defect report, failing test command, and red/green evidence are already sufficient.

# Output Contract

Return regression test coverage with:

- `mode_selected` (bug-fix regression, security regression, refactor characterization, hard-to-reproduce defect, or existing-evidence reuse)
- `boundaries_inspected` (changed source, existing tests, fixtures, generated inputs, bug report, incident notes, same-pattern paths, CI gate, and skipped boundaries with reason)
- `defect_reference` (defect ID, incident reference, or PR/review link)
- `failure_reproduction` (exact triggering conditions: input, state, role, timing, dependencies)
- `test_level` (Unit / Integration / E2E — justified per level selection matrix)
- `red_before_fix_verification` (confirmation that test fails on pre-fix code; failure mode matches original defect)
- `test_code` (test file, test name, arrange/act/assert; defect link in comment)
- `fixture_design` (mirrors production data patterns; covers exact triggering conditions)
- `test_link` (CI integration; PR gate requirement)
- `graph_memory_execution_freshness` (repository graph, project memory, old CI/test report, and prior agent claims accepted, rejected, stale, or not verified)
- `validation_freshness` (literal command, working directory, exit code, artifact/report path, latest edit coverage, and stale/not-run scope)
- `tool_permission_boundary` (shell/test runner/CI/connector action class, sandbox/approval state, write scope, and secret-output redaction rule)
- `untestable_documentation` (if applicable: defect reference, impossibility reason, residual risk, compensating controls, reviewer sign-off)
- `mutation_test_validation` (optional: mutation testing result confirming test fails when defect mutation applied)

# Evidence Contract

A regression test is accepted only when the output includes:

- **Defect basis**: defect ID, incident, review finding, exploit, failing user scenario, or exact failure report.
- **Red-before-fix evidence**: command, commit/branch state, failure output, and why the failure matches the original defect.
- **Green-after-fix evidence**: command, output, changed assertion path, and confirmation that the same test now passes.
- **Triggering condition**: exact input, state, role, timing, dependency response, feature flag, or data shape that originally caused the bug.
- **Source freshness**: current source, tests, fixtures, generated inputs, repository graph, project memory, prior CI output, and old agent reports accepted, rejected, stale, or not verified.
- **What evidence proves**: the specific recurrence path is blocked.
- **What evidence does not prove**: adjacent variants, concurrency paths, production-only dependencies, load behavior, or untested clients.
- **Residual risk**: untested variants, flaky or non-deterministic paths, impossible automated test rationale, owner, and compensating control.

# Quality Gate

The regression test coverage is complete only when:

1. Test is RED on pre-fix code for the same failure mode as the original defect.
2. Test is GREEN on post-fix code.
3. Test captures exact triggering conditions from the defect report (not simplified).
4. Test is at the narrowest level that would have caught the defect.
5. Test has a defect reference comment linking to the source defect or incident.
6. If untestable: defect reference, impossibility reason, residual risk, and compensating control are documented.
7. Test does not depend on timing, network, or external state without a deterministic substitute.
8. Security defects: test reproduces the specific attack vector (not just the absence of authorization).
9. Test is integrated into CI and required as a merge gate.
10. Mutation testing (if run) confirms the test fails when the defect mutation is applied.
11. Current source, fixtures, generated inputs, repository graph, project memory, and old CI/agent claims are reconciled before closure.
12. Validation report names command, exit code, artifact path, freshness after final edit, and what the evidence does not prove.

# Used By

- quality-test-gate
- ai-code-review-refactor

# Handoff

Hand off to the relevant test-level capability (unit-testing, integration-testing, or e2e-testing) for test infrastructure and framework guidance; `failure-diagnosis` when root cause analysis is needed before the regression test can be written; `test-data-management` when the triggering condition requires complex fixture data or database state setup.

# Completion Criteria

The capability is complete when **every confirmed defect has automated reproduction evidence that was red before the fix and green after, or has a documented impossibility statement with residual risk and compensating control, and every regression test is linked to its source defect and integrated into the merge gate**.
