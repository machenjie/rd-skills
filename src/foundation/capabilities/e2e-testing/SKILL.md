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

Anchor against: **Playwright** (Microsoft) — leading cross-browser E2E framework; auto-wait, network interception, trace viewer, component testing, parallel workers. **Cypress** — popular browser-native E2E framework; real-time reload, time-travel debugging; strong ecosystem. **WebdriverIO** — W3C WebDriver protocol; multi-browser, mobile (Appium) support. **Selenium Grid / WebDriver** — legacy standard; still dominant in enterprise regulated environments. **Google Testing Blog — Testing Trophy** (Kent C. Dodds adaptation) — integration tests provide the best ROI; E2E tests are the peak of the trophy (few but high value). **OWASP Testing Guide v4.2** — auth, session, access control, and business logic test cases map directly to high-priority E2E journeys. **DORA metrics** — E2E suite execution time contributes to CI lead time; must not exceed 10 minutes on standard runner. **Selenium Grid 4 / Playwright Grid** — parallel multi-browser execution; required for sub-10-minute full-suite runs. **Percy / Chromatic** — visual regression testing integrated into E2E; snapshot diffing for UI component stability. **Axe-core in Playwright** — accessibility assertions within E2E journey tests (`checkA11y`). **Page Object Model (POM)** — abstraction pattern; encapsulates selectors and actions per page; reduces selector duplication across tests. **App Actions Pattern** (Cypress philosophy) — prefer API/backend setup over UI setup for test data; avoid "login via UI" for every test; use programmatic auth (cookie injection, JWT setup).

### Journey Priority Matrix

| Journey category | Risk | E2E priority | Alternative if no E2E |
| --- | --- | --- | --- |
| Login / authentication | Critical | Must have | Integration test for auth middleware |
| Permission gate (deny path) | Critical | Must have | Integration test with auth mock |
| Checkout / payment confirmation | Critical | Must have | Integration + contract test |
| Onboarding multi-step wizard | High | Recommended | Integration + component test |
| Destructive action (delete, cancel) | High | Recommended | Integration test with side-effect assertion |
| Password reset / account recovery | High | Recommended | Integration test for email flow |
| Core CRUD user flow | Medium | Optional | Integration test is sufficient |
| Search and filter | Medium | Optional | Component + integration test |
| Static / informational pages | Low | Skip | Visual regression snapshot only |
| Admin configuration screens | Low | Optional | Integration test for API |

### Selector Strategy Priority

```
Priority 1 (Preferred): ARIA-semantic locators
  page.getByRole('button', { name: 'Confirm Order' })
  page.getByLabel('Email address')
  page.getByText('Your order has been placed', { exact: true })

Priority 2 (Acceptable): Explicit test IDs
  page.locator('[data-testid="submit-order-btn"]')

Priority 3 (Avoid): CSS class or structural selectors
  page.locator('.btn-primary')           ← breaks on style refactor
  page.locator('div:nth-child(3) > a')  ← breaks on layout change
  page.locator('//button[@class="..."]') ← XPath; brittle

Rule: Add data-testid to elements ONLY when no ARIA-semantic locator
is available AND the element is exercised by a required E2E test.
Never add data-testid preemptively; add them when the test needs them.
```

### Test Data Isolation Pattern

```
// BAD: shared test account — causes order dependency
await page.goto('/login');
await page.fill('[data-testid="email"]', 'testuser@shared.com');

// GOOD: per-test isolated user created via API
const user = await createTestUser(apiClient, { role: 'buyer' });
await setAuthCookie(page, user.sessionToken);  // skip UI login
test.afterEach(async () => { await deleteTestUser(apiClient, user.id); });

// WHY: UI login in every test adds 3-5s per test; with 50 tests = 4 min overhead
// Use App Actions (API setup) for everything except the login journey itself
```

### Flake Control Checklist

| Cause | Detection | Fix |
| --- | --- | --- |
| Race condition (animation, async render) | Flake without network throttle | Replace `waitForTimeout` with `expect(locator).toBeVisible()` |
| Shared test data | Fails when run in parallel | Per-test data creation + teardown |
| External API latency | Timeout flake in CI | Mock or stub external API; use `route.fulfill()` |
| Browser fingerprint / rate limit | Fails only in CI | Rotate user-agent; use API auth setup |
| Selector coupled to changing text | Fails on copy change | Use `data-testid` or role-based selector |
| Non-deterministic data order | Assertion on wrong item | Sort data before assertion; use specific item ID |

# Selection Rules

Select this capability when the **assembled user journey through multiple system layers** is the primary risk. Adjacent routing:

- Prefer `frontend-testing` for component behavior, visual regression, and route-level tests that do not cross service boundaries.
- Prefer `integration-testing` when service-layer interaction (API + DB) is the risk, not the full browser flow.
- Prefer `contract-testing` when API compatibility across services is the risk.
- Prefer `regression-testing` when the primary concern is preventing regressions in well-defined behavior.
- Prefer `test-strategy` when determining the right balance of E2E vs integration vs unit coverage for a new feature.

# Risk Escalation Rules

Escalate when: no E2E test exists for a login or authentication flow being changed; no coverage for permission-denied path on a sensitive resource; a payment or financial confirmation flow has no E2E evidence; a multi-step onboarding flow with no test is being modified; the E2E suite has > 30% flaky tests that are unquarantined; the suite takes > 20 minutes on CI and is blocking deployments.

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

# Output Contract

Return an E2E plan with:

- `journey_name` and `business_risk` (why this journey merits E2E coverage)
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

# Used By

- quality-test-gate
- frontend-change-builder

# Handoff

Hand off to `test-strategy` for overall coverage balance; `frontend-testing` for component and route tests; `test-data-management` for complex data isolation strategy; `observability` for production smoke tests and post-release monitoring; `regression-testing` for non-journey behavioral regression coverage.

# Completion Criteria

The capability is complete when **critical user journeys are covered by a narrow, stable, deterministic E2E suite** with semantic selectors, isolated test data, business-outcome assertions, auth/permission branches, and CI artifact capture — without duplicating lower-level test coverage or growing to unsustainable size.
