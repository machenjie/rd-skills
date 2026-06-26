---
name: e2e-testing
description: Verifies critical user journeys, authentication, permissions, and failure paths through narrow stable end-to-end coverage.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "62"
changeforge_version: 0.1.0
---

# Mission

Prove that **critical user journeys execute correctly through the assembled system** — covering authentication, authorization, multi-step workflows, checkout, and high-risk failure paths — while keeping E2E coverage narrow, stable, and deterministic enough to run on every CI commit without becoming the dominant cost in the test suite.

# When To Use

Use this capability when a change affects: primary user journeys spanning multiple routes or views; login, logout, session expiry, MFA, or OAuth flows; role-based permission gates (access granted / access denied); checkout, payment, or financial confirmation flows; onboarding multi-step sequences; destructive or irreversible actions (delete account, cancel subscription, purge data); high-revenue or compliance-regulated workflows; real-time or async feedback loops (email confirmation, webhook receipt, notification delivery); or recovery flows (reset password, error retry, partial-save resumption).

# Do Not Use When

Do not use this capability to cover every permutation of input or every component state — those are the domain of unit testing and component testing. Do not use it to re-prove rules already validated by integration or contract tests (asserting HTTP status codes from an E2E test that already has integration test coverage wastes time and creates flake). Do not add E2E tests for flows where the risk profile is low and a fast integration test is sufficient.

# Stage Fit

Use during planning, testing, code review, and validation when assembled browser behavior, route transitions, auth state, permissions, side effects, or CI artifacts decide release confidence. Repository graph, project memory, and prior agent trajectory can suggest existing journeys or flaky zones, but current source, routes, tests, fixtures, and CI output must confirm that evidence is fresh before reuse.

# Non-Negotiable Rules

- **Select only critical journeys and high-risk branches for E2E coverage.** The E2E suite must stay small enough to give a result in under 10 minutes in a standard CI runner. If the suite grows beyond this, it must be parallelized across browser workers, not expanded unchecked.
- **Stable, semantic selectors only.** Use `data-testid` attributes or ARIA-role locators (`getByRole('button', { name: 'Submit' })`) as the canonical selector strategy. CSS class names, element indices, and XPath expressions are forbidden as primary selectors — they couple tests to visual implementation and break on any refactor. Playwright `getByRole`, `getByLabel`, `getByText` (exact match) are preferred.
- **Test data is owned and isolated per test.** Every test creates (or seeds via API/DB setup) the exact data it needs and tears it down on completion. No test may read or write to shared persistent test accounts or shared database rows that another test also touches. Shared state is the primary cause of order-dependent failures.
- **No arbitrary sleeps.** `await page.waitForTimeout(2000)` is prohibited. Use `await expect(locator).toBeVisible()`, `waitForResponse`, `waitForSelector`, or application-level readiness signals. Arbitrary waits hide race conditions and make tests 3-5× slower than necessary.
- **Assert user-visible outcomes and durable side effects.** A journey that checks "the URL changed to /dashboard" has not proven the journey succeeded. Assert: the confirmation message the user sees, the record that was created (via API check or DB assertion), the email that was sent (via test mailbox), or the event that was emitted. Side-effect assertions prove the journey's business purpose.
- **Include auth expiry and permission-denial paths in coverage.** At least one E2E test must cover: valid login succeeds; invalid credentials fails with correct message; session expiry redirects to login; role without permission sees denied state (not just 404). These paths are disproportionately high-risk and often untested.
- **Capture trace, screenshot, and video on failure.** Every CI E2E runner must be configured to capture Playwright traces (`.zip`), screenshots, and optionally video on test failure. Without these artifacts, diagnosing a failure in headless CI is practically impossible.
- **Define a flake quarantine policy.** A test that fails intermittently (flakes) in CI must be quarantined within 48 hours of detection. Quarantine = tagged `@flaky`, moved to a non-blocking CI step, assigned an owner, and given a deadline. Unquarantined flaky tests erode trust in the entire suite faster than any feature addition.

# Industry Benchmarks

Anchor against Playwright auto-wait/tracing, Cypress browser-native debugging, WebDriver/Selenium Grid enterprise browser coverage, Testing Trophy layer selection, OWASP auth/session/access-control journey coverage, DORA CI lead-time pressure, visual regression tools, axe-core checks, Page Object discipline, and App Actions data setup. Keep the body focused on routing and evidence; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for journey priority, selector, data-isolation, flake-control, graph/memory/execution, and framework-specific details.

# Selection Rules

Select this capability when the **assembled user journey through multiple system layers** is the primary risk. Adjacent routing:

- Prefer `frontend-testing` for component behavior, visual regression, and route-level tests that do not cross service boundaries.
- Prefer `integration-testing` when service-layer interaction (API + DB) is the risk, not the full browser flow.
- Prefer `contract-testing` when API compatibility across services is the risk.
- Prefer `regression-testing` when the primary concern is preventing regressions in well-defined behavior.
- Prefer `test-strategy` when determining the right balance of E2E vs integration vs unit coverage for a new feature.

# Risk Escalation Rules

Escalate when: no E2E test exists for a login or authentication flow being changed; no coverage for permission-denied path on a sensitive resource; a payment or financial confirmation flow has no E2E evidence; a multi-step onboarding flow with no test is being modified; the E2E suite has > 30% flaky tests that are unquarantined; the suite takes > 20 minutes on CI and is blocking deployments.

# Proactive Professional Triggers

- **Signal:** Auth, session expiry, MFA, OAuth, tenant, or permission-gated navigation changes are covered only by component or API tests.
  **Hidden risk:** assembled cookies, redirects, role gates, or denied journeys can be wrong while lower layers pass.
  **Required professional action:** require one narrow E2E journey for the changed auth/permission path or document why integration coverage is sufficient.
  **Route to:** `e2e-testing`, `security-privacy-gate`, `frontend-testing`.
  **Evidence required:** journey map, allowed and denied branch, command with exit code or not-run disclosure, trace or screenshot artifact.
- **Signal:** Checkout, destructive action, data export, onboarding, or recovery journey asserts only navigation or visible text.
  **Hidden risk:** the user sees success while the durable order, deletion, export, audit event, email, or retry state is missing.
  **Required professional action:** add a side-effect assertion or route the lower-level integration proof that makes E2E unnecessary.
  **Route to:** `integration-testing`, `test-data-management`, `quality-test-gate`.
  **Evidence required:** persisted state/API/email/event assertion, fixture owner, teardown proof, and evidence-limit note.
- **Signal:** E2E tests use shared accounts, live external providers, CSS/XPath selectors, arbitrary sleeps, or unowned test data.
  **Hidden risk:** flaky or unsafe tests hide real regressions, leak data, or block releases with non-diagnostic failures.
  **Required professional action:** require rewriting with isolated fixtures, semantic selectors, deterministic waits, and provider stubs before gate closure.
  **Route to:** `test-data-management`, `frontend-testing`, `validation-broker`.
  **Evidence required:** selector strategy, data cleanup path, stub matrix, CI artifact, and flake/quarantine owner.
- **Signal:** Repository graph, project memory, old CI output, or prior agent notes suggest reusing an E2E pattern or known flaky journey.
  **Hidden risk:** stale routes, renamed fixtures, changed CI config, or unrepaired prior failures make reused evidence unverified.
  **Required professional action:** inspect current source/tests/routes/CI and verify freshness before accepting the pattern or mark it stale.
  **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `plan-execution-consistency`.
  **Evidence required:** inspected paths, accepted/rejected pattern, freshness limit, command/report path, and residual owner.
- **Signal:** E2E is proposed as the only proof for local business rules, field permutations, or a growing broad suite.
  **Hidden risk:** slow browser coverage replaces faster unit/integration/regression evidence and hides missing branch tests.
  **Required professional action:** split local logic to lower test levels and keep E2E only for the critical journey.
  **Route to:** `test-strategy`, `regression-testing`, `quality-test-gate`.
  **Evidence required:** risk-to-layer map, omitted-level rationale, CI runtime or flake budget, and changed-code-to-test map.

# Critical Details

E2E tests are the most expensive tests to write, maintain, and debug. Precision failures that destroy E2E value:

- **Test as documentation failure.** A test named `test('form works')` that clicks through 12 steps without asserting business outcomes is valueless. Every E2E test must assert the observable outcome the user cares about — the confirmation message, the record in the database, the email received.
- **UI login amplification.** If every test starts with `await loginViaUI(page)`, a 50-test suite spends 4 minutes just logging in. Use Playwright `storageState` (auth state pre-saved) or API cookie injection to skip the login UI for all tests except the login journey itself.
- **Network dependency without mocking strategy.** Tests that call live external APIs (Stripe, SendGrid, Twilio) in CI introduce non-determinism, rate limit failures, and cost. Stub external APIs using `page.route()` (Playwright) or `cy.intercept()` (Cypress) for all external dependencies. Test only the paths the external API can take: success, failure, timeout.
- **Missing teardown.** A test that creates a user, places an order, and creates a charge but doesn't tear down leaves orphaned data. Over 1000 CI runs, this becomes a data pollution problem that causes other tests to fail unexpectedly.
- **Assertion stops at navigation.** `expect(page.url()).toBe('/order-confirmation')` proves the URL changed, not that the order was placed. Add: `await expect(page.getByTestId('order-number')).toBeVisible()` and `const order = await getOrderByUser(user.id); expect(order.status).toBe('PLACED')`.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `await page.waitForTimeout(3000)` | Hides race conditions; adds 3s minimum to every run; flaky on slow CI |
| `page.locator('.btn-primary')` as primary selector | Breaks on any CSS refactor; not semantic |
| Shared `testuser@example.com` across all tests | Order-dependent; parallel test failures; non-deterministic |
| `test('login works')` — no assertion beyond URL change | Proves navigation, not authentication success |
| 200 E2E tests covering every field variant | Duplicates unit tests; suite takes 45 min; rarely run; flaky |
| No `data-testid` or ARIA selector strategy | Tests break on any design-system component rename |
| External Stripe API called in CI E2E test | Rate limited; real charges created; non-deterministic response time |
| No trace/screenshot on failure | Impossible to diagnose headless CI failures; wasted investigation time |

# Failure Modes

- E2E suite reaches 400 tests covering every permutation; takes 55 minutes on CI; engineers stop waiting for results; confidence collapses.
- Shared test account `qa@example.com` causes 30% of tests to fail when run in parallel because concurrent tests mutate shared state.
- Login journey test only asserts URL change; auth middleware bug ships to production; test passes because URL was correct.
- Flaky animation race: `waitForTimeout(500)` passes locally (fast machine) but fails on CI (slow runner); quarantine never applied; suite red for 2 weeks.
- External Stripe API called without mocking; Stripe rate-limits CI runner; 20 payment tests fail; deploy blocked.
- Test teardown missing; orphaned test orders trigger billing notifications to test email; support tickets created.
- `page.locator('.submit-btn')` breaks after design-system component rename from `submit-btn` to `btn-submit`; 60 tests fail simultaneously.
- No permission-denied E2E test; RBAC middleware bug ships; admin-only endpoint accessible to regular users.
- Missing trace artifacts; intermittent failure in CI; engineer spends 3 hours adding logs to reproduce locally.

# Reference Loading Policy

The body carries L1/L2 E2E selection, routing, output, and quality-gate rules. Load [references/checklist.md](references/checklist.md) when the change touches critical user journeys, auth/session flows, permission denial, checkout/payment confirmation, destructive actions, external stubs, flake policy, or CI browser artifacts. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when journey priority, selector strategy, data isolation, flake triage, framework choice, or graph/memory/execution freshness needs detail. Use [examples/example-output.md](examples/example-output.md) only when the output shape is unclear. Do not load deep references when lower-level unit, integration, or contract evidence is sufficient for the stated risk.

# Output Contract

Return an E2E plan with:

- `journey_name` and `business_risk` (why this journey merits E2E coverage)
- `mode_selected` (critical journey, auth/permission branch, side-effect journey, flake repair, or evidence reuse)
- `source_evidence` (current routes, tests, fixtures, CI config, repository graph, project memory, or prior agent output inspected with freshness limits)
- `user_role(s)` and `permission_level` required
- `test_data_strategy` (API setup, DB seed, or UI setup; isolation mechanism; teardown plan)
- `auth_strategy` (storageState, cookie injection, or UI login with justification)
- `steps` (numbered; user action + expected system response at each step)
- `primary_assertion` (user-visible outcome: message, redirect, element content)
- `side_effect_assertion` (DB record, API state, email, event — proves business outcome)
- `permission_denied_branch` (if applicable: role without access, expected denied state)
- `auth_failure_branch` (invalid token, expired session, wrong credentials)
- `failure_recovery_branch` (network error, validation failure, retry behavior)
- `external_api_stubs` (which external services are stubbed; stub strategy per response type)
- `selector_strategy` (ARIA-semantic or data-testid; no CSS class selectors)
- `flake_controls` (waitFor strategy, no arbitrary timeouts, deterministic data)
- `ci_configuration` (parallelism workers, browser matrix, trace/screenshot/video on failure)
- `artifacts` (trace zip, screenshot, video; where stored in CI)
- `validation_evidence` (command, working directory, exit code, artifact path, freshness after final edit, and not-run scope)

# Evidence Contract

An E2E test is accepted only when the output includes:

- **User journey**: actor, entry point, full path, expected outcome, and business value.
- **Layer justification**: why unit, integration, or contract tests are insufficient.
- **State setup**: test data owner, environment, feature flags, authentication state, and cleanup.
- **Observable assertions**: user-visible state, accessibility state, persisted result, network result, notification, or audit record.
- **Stability controls**: deterministic waits, retry policy, fixture isolation, and flake mitigation.
- **Source freshness**: current source, routes, tests, fixtures, CI config, repository graph, project memory, old CI reports, and prior agent claims accepted, rejected, stale, or not verified.
- **Flake budget**: expected stability and quarantine/triage plan if the test is flaky.
- **Validation evidence**: command, working directory, exit code, artifact path, and freshness after latest material edit.
- **What evidence proves**: the named end-to-end journey works through the selected environment.
- **What evidence does not prove**: all browsers/devices/locales, production scale, third-party production behavior, alternate roles, or untested journeys.
- **Residual risk**: untested journey variants, owner, and next gate.

# Quality Gate

The E2E plan is complete only when:

1. Every test covers a journey with documented business risk justification.
2. All selectors use ARIA-semantic or `data-testid` strategy; no CSS class or index selectors.
3. Test data is per-test isolated with explicit teardown; no shared state.
4. No `waitForTimeout` in any test; all waits use `expect(locator).toBeVisible()` or event-based waits.
5. Primary assertion covers user-visible outcome; side-effect assertion covers business outcome (DB/API/email).
6. Auth expiry and permission-denied paths covered for any auth-gated journey.
7. External APIs stubbed; no live external API calls in E2E CI runs.
8. CI configured to capture trace, screenshot, and video on failure.
9. Flake quarantine policy defined; max CI run time target documented (≤ 10 min standard; ≤ 20 min with parallelism).
10. Suite size justified: each test maps to a journey in the journey priority matrix.
11. Repository graph, project memory, old CI output, and prior agent claims are source-confirmed or marked stale/not verified before reuse.
12. Validation evidence names command, exit code, artifact path, freshness, and what the E2E result does not prove.

# Used By

- quality-test-gate
- frontend-change-builder

# Handoff

Hand off to `test-strategy` for overall coverage balance; `frontend-testing` for component and route tests; `test-data-management` for complex data isolation strategy; `observability` for production smoke tests and post-release monitoring; `regression-testing` for non-journey behavioral regression coverage; `repository-context-map`, `repository-graph-analysis`, and `project-memory-governance` when reused journeys or prior failures need freshness checks; and `validation-broker` when changed paths must map to narrow/module/full browser validation commands.

# Completion Criteria

The capability is complete when **critical user journeys are covered by a narrow, stable, deterministic E2E suite** with semantic selectors, isolated test data, business-outcome assertions, auth/permission branches, and CI artifact capture — without duplicating lower-level test coverage or growing to unsustainable size.
