# E2E Benchmarks And Patterns

Use this reference only when the E2E decision needs more detail than the `SKILL.md` body: journey priority, selector tradeoffs, test data isolation, flake diagnosis, framework choice, or freshness checks for repository graph and project memory.

## Framework Anchors

- **Playwright:** cross-browser runner with auto-wait, network interception, trace viewer, parallel workers, storage state, and component testing.
- **Cypress:** browser-native runner with time-travel debugging and a strong intercept ecosystem.
- **WebdriverIO / Selenium Grid:** W3C WebDriver-based coverage for enterprise browser and Appium/mobile environments.
- **Testing Trophy:** prefer unit/integration tests for local logic; keep E2E at the top for a few high-value journeys.
- **OWASP Testing Guide:** auth, session, access control, and business logic cases map to high-priority E2E journeys when browser orchestration is the risk.
- **DORA lead-time pressure:** E2E runtime is part of CI lead time; slow suites must be parallelized or narrowed.
- **Percy / Chromatic:** visual regression checks can complement E2E for layout-sensitive states but do not prove business side effects.
- **Axe-core:** accessibility checks can run inside browser journeys when a critical flow includes interactive forms, modals, or dynamic status.
- **Page Object / Screenplay patterns:** encapsulate selectors and repeated actions, but do not hide business assertions.
- **App Actions:** prefer API/backend setup for data and auth except when the setup flow itself is the journey under test.

## Journey Priority Matrix

| Journey category | Risk | E2E priority | Alternative if no E2E |
| --- | --- | --- | --- |
| Login / authentication | Critical | Must have when changed | Integration test for auth middleware |
| Permission gate denied path | Critical | Must have when changed | Integration test with auth fixture |
| Checkout / payment confirmation | Critical | Must have for primary flow | Integration + contract test |
| Onboarding multi-step wizard | High | Recommended | Integration + component test |
| Destructive action delete/cancel | High | Recommended | Integration test with side-effect assertion |
| Password reset / account recovery | High | Recommended | Integration test for email/token flow |
| Core CRUD user flow | Medium | Optional | Integration test is usually sufficient |
| Search and filter | Medium | Optional | Component + integration test |
| Static or informational page | Low | Skip | Visual regression only if layout risk exists |
| Admin configuration screen | Low/Medium | Optional by blast radius | API/integration test for configuration effect |

## Selector Strategy Priority

1. Prefer ARIA-semantic locators:

```ts
page.getByRole("button", { name: "Confirm Order" });
page.getByLabel("Email address");
page.getByText("Your order has been placed", { exact: true });
```

2. Use explicit test IDs only when the element has no reliable accessible locator:

```ts
page.locator('[data-testid="submit-order-btn"]');
```

3. Avoid CSS, index, and XPath selectors as primary selectors:

```ts
page.locator(".btn-primary");
page.locator("div:nth-child(3) > a");
page.locator("//button[@class='...']");
```

Add `data-testid` only when a required E2E test needs it and no semantic locator is available.

## Test Data Isolation Pattern

Shared test account pattern to reject:

```ts
await page.goto("/login");
await page.fill('[data-testid="email"]', "testuser@shared.com");
```

Per-test isolated setup pattern:

```ts
const user = await createTestUser(apiClient, { role: "buyer" });
await setAuthCookie(page, user.sessionToken);
test.afterEach(async () => {
  await deleteTestUser(apiClient, user.id);
});
```

Use UI login only for the login journey itself. For other journeys, storage state or API cookie injection avoids repeated 3-5 second setup and prevents unrelated login failures from masking the target journey.

## Flake Control Checklist

| Cause | Detection | Fix |
| --- | --- | --- |
| Animation or async render race | Fails under slow CI or throttling | Replace timeout with locator/event readiness |
| Shared data | Fails when tests run in parallel | Create and clean up per-test data |
| External API latency | Timeout or provider error in CI | Stub provider responses and test success/failure/timeout cases |
| Browser fingerprint or rate limit | Fails only in CI | Use controlled auth/data setup and provider stubs |
| Copy-coupled selector | Fails on harmless text update | Use role/name when label is the contract, otherwise test ID |
| Non-deterministic order | Assertion targets wrong row/card | Sort data or assert by unique identifier |

## Graph, Memory, And Execution Freshness

- Treat repository graph and project memory as leads, not proof.
- Confirm current route names, test file locations, fixture ownership, CI browser matrix, and artifact paths before reusing old E2E evidence.
- Reject prior agent claims when the claim lacks command, exit code, artifact path, changed-path mapping, or freshness after the latest edit.
- If a known flaky journey appears in memory, require owner, quarantine status, reproduction signature, and remediation deadline before counting it as coverage.
- If an E2E pattern is copied from another module, inspect whether auth, permissions, tenant scope, external stubs, and teardown semantics still match the current surface.
