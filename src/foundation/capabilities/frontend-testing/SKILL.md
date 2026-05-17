---
name: frontend-testing
description: Defines frontend tests around user-visible behavior, roles, permissions, error states, and core flows instead of implementation details alone.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "36"
changeforge_version: 0.1.0
---

# Mission

Design frontend verification that **proves user-visible behavior, role and permission states, error recovery, and accessibility** — not implementation internals — so that tests fail when the user experience breaks and survive harmless refactors, using the right test level for each behavior class.

# When To Use

Use this capability when a frontend change: adds or modifies components, routes, or views that users interact with; introduces role- or permission-differentiated rendering; adds loading, empty, error, success, disabled, or stale states; changes form field validation or submission behavior; integrates with an API that affects what users see or can do; introduces accessibility interactions (keyboard navigation, focus management, ARIA roles); or adds critical user flows that span multiple components.

# Do Not Use When

Do not use this capability for pure logic utilities with no DOM output — use unit testing. Do not use it for complete browser journeys across multiple pages and services — use `e2e-testing`. Do not use it for server-rendered HTML rendering logic in backend templates — use backend testing.

# Non-Negotiable Rules

- **Test user-observable behavior, not implementation structure.** Assertions must target what users see and can do: rendered text, visible buttons, form fields, navigation links, accessible labels, validation messages. Do not assert: component state variable names, internal function call counts, CSS class names (unless they encode semantic meaning), or React prop values that are not reflected in the DOM.
- **Use accessible queries.** Testing Library query priority: `getByRole` (first choice for interactive elements), `getByLabelText` (forms), `getByPlaceholderText` (when label unavailable), `getByText`, `getByDisplayValue`, `getByAltText`, `getByTitle`; use `getByTestId` only as last resort and only with `data-testid` attributes (never CSS class or element selectors). Never use `querySelector('.btn-primary')` — brittle; breaks on style refactor.
- **Every permission state must have a test fixture.** If a component renders differently for admin vs member vs viewer roles, each role must have a test case. Do not test only the highest-privilege view and assume lower privilege works.
- **API mocks must match the contract.** Mocked API responses must be consistent with the dto-schema / OpenAPI contract. Use contract-aligned fixtures, not hand-crafted objects. A mock that diverges from the real response shape creates a false safety net — tests pass, production fails.
- **Error and empty states must be tested for recovery.** Testing an error state means: (1) render the error state; (2) assert the error message is visible and correct; (3) assert the recovery action (retry button, back link) is present and functional. Snapshotting an error state without asserting recovery action is incomplete.
- **Loading states must not cause test flakiness.** Do not `await` arbitrary timeouts to wait for async behavior. Use `await screen.findByText(...)` (waits for element to appear) or `waitFor(() => expect(...))`. Never use `await new Promise(resolve => setTimeout(resolve, 500))` in tests.
- **Coverage targets are secondary to behavior completeness.** A 95% line coverage achieved by testing `getProps()` methods is not better than 70% coverage that tests all critical user flows. Coverage is a floor signal, not a quality signal. What matters: are the user journeys and risk states covered?

# Industry Benchmarks

Anchor against: **Testing Library** (Kent C. Dodds; `@testing-library/react`, `@testing-library/vue`, `@testing-library/svelte`) — guiding principle: "The more your tests resemble the way your software is used, the more confidence they give you"; accessible query priority; `userEvent` over `fireEvent` for realistic interactions. **Vitest** (Vite ecosystem) — fast ESM-native unit/integration test runner; compatible with Testing Library; `vi.mock()`, `vi.spyOn()`. **Jest** — mature test runner; `jest.mock()`, `jest.spyOn()`; `msw` integration for API mocking. **Mock Service Worker (MSW)** — intercepts `fetch`/`XMLHttpRequest` at the network level (Service Worker in browser; `http.Handler` in Node.js); contract-aligned response mocking; preferred over mocking fetch directly or mocking entire HTTP client modules. **Storybook + Chromatic** — component documentation + visual regression testing; screenshot comparison across branches; Interaction Tests (`play()` function) for within-story user interactions. **axe-core / jest-axe** — automated WCAG 2.2 accessibility rule checking; `expect(container).toHaveNoViolations()` after render; catches: missing labels, insufficient color contrast (basic), broken ARIA roles, missing alt text. **React Testing Library user-event v14** — simulates real browser events: pointer events, keyboard navigation, clipboard; more realistic than v13 `userEvent`; `userEvent.setup()` for instance-based API. **Testing Trophy** (Guillermo Rauch, Guillermo Rauch pattern; Kent C. Dodds) — integration tests provide highest ROI for frontend; unit tests for pure logic; E2E for critical smoke paths only; avoid testing implementation details. **WCAG 2.2 Level AA** — 2.4.3 Focus Order, 2.4.7 Focus Visible, 4.1.2 Name Role Value — verify with keyboard navigation tests. **Storybook Interaction Tests** — `play()` function with `userEvent` for within-story behavior; `@storybook/addon-interactions`; CI mode with `storybook/test-runner`.

### Test Level Decision Matrix

| Behavior to test | Recommended level | Tool | Why |
| --- | --- | --- | --- |
| Single component rendering | Component integration test | Testing Library + Vitest/Jest | Fast; tests DOM output; not implementation |
| Form validation UX (field errors, submit) | Component integration test | Testing Library + MSW | Can verify field-level messages and recovery |
| Permission-differentiated rendering | Component integration test | Testing Library + role fixtures | Fast; exhaustive across roles |
| Multi-component data flow (parent → child) | Component integration test | Testing Library (render parent) | Prefer rendering the full sub-tree |
| Async data loading states | Component integration test | Testing Library + MSW | Mock network; assert loading/success/error |
| Core user flow (3+ steps, 1 page) | Integration test | Testing Library + MSW | Tests realistic path without full browser |
| Cross-page navigation flow | E2E test | Playwright / Cypress | Requires real browser routing |
| Pure utility function | Unit test | Vitest / Jest | No DOM; pure logic |
| Visual regression | Visual snapshot | Storybook + Chromatic | Screenshot diff; catches layout breaks |
| WCAG accessibility rules | Accessibility test | jest-axe / axe-core | Automated ARIA/label/role checking |

### State Coverage Checklist

Every component or view with dynamic behavior must have test coverage for applicable states:

```
Rendering states:
  □ Loading (skeleton, spinner, progress indicator visible)
  □ Success (data rendered correctly)
  □ Empty (no data; empty state message; create action if applicable)
  □ Error (error message; recovery action present and functional)
  □ Stale (stale data indicator if applicable)

Permission states:
  □ Each role variant that changes visible elements or available actions
  □ Unauthenticated (redirect to login; no protected content visible)
  □ Permission-denied (403 state; no access message; correct recovery)

Interaction states:
  □ Disabled (button/field disabled; correct reason communicated)
  □ In-progress/loading (button shows loading; no double-submit possible)
  □ Validation error (field-level; form-level; recovery by correcting input)
  □ Confirmation required (destructive action; confirm dialog shown)

Accessibility states:
  □ Focus management (focus moves to expected element after action)
  □ Keyboard navigation (Tab order; Enter/Space on buttons; Escape on dialogs)
  □ Screen reader labels (accessible name on all interactive elements)
  □ No axe-core violations (jest-axe assertion on render)
```

### API Mock Alignment Pattern

```typescript
// BAD — hand-crafted mock that may diverge from contract
jest.mock('../api/users', () => ({
  fetchUser: jest.fn().mockResolvedValue({ id: '1', name: 'Alice' })
}));
// Risk: API adds required field 'email'; mock silently missing; test passes; production fails

// GOOD — MSW with contract-aligned fixture
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { userFactory } from '../test-factories/user';

it('renders user email', async () => {
  server.use(
    http.get('/api/users/:id', () => {
      // userFactory uses Zod schema or OpenAPI-derived type — contract-aligned
      return HttpResponse.json(userFactory.build({ email: 'alice@example.com' }));
    })
  );
  render(<UserProfile userId="1" />);
  expect(await screen.findByText('alice@example.com')).toBeInTheDocument();
});
```

# Selection Rules

Select this capability when **frontend component and integration testing strategy** is the primary design concern. Adjacent routing:

- Prefer `e2e-testing` when complete browser journeys spanning multiple pages and services need to be validated.
- Prefer `unit-testing` when the test subject is a pure logic function with no DOM or component behavior.
- Prefer `contract-testing` when the primary risk is API response shape divergence between frontend mock and backend implementation.
- Prefer `accessibility-testing` when a comprehensive WCAG audit across the full application is required.

# Risk Escalation Rules

Escalate when the change touches: authentication or authorization flows (login, token refresh, permission gates); payment or checkout UI; destructive actions (delete account, bulk delete, data export); accessibility-critical interactions in regulated (WCAG AA required) products; cross-browser behavior differences (use E2E for these); or features with contractual SLAs on uptime.

# Critical Details

Frontend tests fail for the wrong reasons when anchored to implementation. Precision failures:

- **Snapshot test false safety.** Snapshot test of the error state captures: `<p className="error-msg">Something went wrong</p>`. The snapshot is "passing." But the retry button that was present 2 weeks ago was removed in an unrelated refactor. The snapshot does not include the retry button. Test still passes. User cannot recover from errors. Snapshot tests must be supplemented with explicit behavioral assertions.
- **`getByTestId` as first choice.** A test uses `getByTestId('submit-btn')` on every button. The submit button label changes from "Submit" to "Place Order" — a legitimate UX improvement. The `data-testid` is unchanged. Test passes. But the user-visible label change was never verified. Use `getByRole('button', { name: 'Place Order' })` — tests both presence and accessible label.
- **Role fixture gap.** Tests use an admin user fixture for all component tests. The component has a permission check: `if (user.role === 'admin') show delete button`. Tests always show the delete button. A viewer accesses the same component via a URL manipulation — delete button renders for viewer. No test caught this.
- **Async `waitFor` with arbitrary timeout.** `await new Promise(resolve => setTimeout(resolve, 500))` in a test. This is a flake generator: on fast CI it passes; on slow CI it times out before the element appears. Use `await screen.findByText('Success')` which retries until the element appears or the default timeout (1000ms) expires.
- **MSW not reset between tests.** Test A registers an MSW handler returning a 500 error. Test B does not reset handlers. Test B inherits the 500 handler. Test B fails with an unexpected API error. Always call `server.resetHandlers()` in `afterEach`.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `getByClassName('submit-btn')` | Breaks on CSS refactor; no semantic meaning tested |
| Snapshot test with no behavioral assertions | Error state "tested" but recovery button absence undetected |
| Only admin fixture used | Permission-denied states untested; authorization bypass undetected |
| `setTimeout(resolve, 500)` in tests | Flaky on slow CI; non-deterministic; masks timing assumptions |
| Mock entire HTTP client module | Mock diverges from contract; tests pass; production fails on API change |
| No `server.resetHandlers()` after each test | Test pollution; intermittent failures across test order |
| Testing internal state variables | Tests break on valid refactor; no user behavior validated |
| 100% coverage from testing getters | Coverage metric satisfied; zero user behavior validated |

# Failure Modes

- Snapshot test of error state passes; retry button removed in refactor; users cannot recover from errors in production.
- Only happy path tested; permission-denied view shows admin content to viewer; security bypass discovered in pentest.
- Mock returns hand-crafted object missing required `role` field; component crashes in production on `user.role.toUpperCase()`.
- `setTimeout(500)` in tests causes 1 in 10 CI runs to fail; PR blocked for flaky test investigation; engineering time wasted.
- MSW handler pollution across tests; test suite passes in isolation; fails 30% of the time in full CI run.
- CSS class-based selectors break when design system migrates from BEM to CSS Modules; 200 tests fail; all require rewrite.
- No keyboard navigation test; Tab order broken by new modal implementation; WCAG 2.4.3 failure found in audit.
- No axe-core assertion; form field label `for` attribute mismatched to field `id`; screen reader users cannot identify field purpose.

# Output Contract

Return a frontend test plan with:

- `user_flows` (list of critical flows to be covered; user-visible start and end states)
- `components_under_test` (component or route name; test level; rationale)
- `state_coverage` (loading/success/empty/error/disabled/stale states to test per component)
- `permission_fixtures` (role variants; what differs per role; test case per variant)
- `api_mock_strategy` (MSW or equivalent; contract-aligned fixture source; reset policy)
- `accessibility_checks` (jest-axe on render; keyboard navigation tests; focus management assertions)
- `query_strategy` (getByRole first; getByLabelText for forms; no CSS class selectors)
- `async_handling` (findBy / waitFor; no setTimeout; AbortController cancellation tests)
- `visual_regression` (Storybook + Chromatic if applicable; which stories; diff threshold)
- `flake_controls` (handler reset; no timeouts; deterministic data; isolated state)
- `coverage_targets` (minimum line/branch coverage; behavior completeness criteria)

# Quality Gate

The test plan is complete only when:

1. Every critical user flow has at least one integration-level test.
2. Every permission variant (role, unauthenticated, permission-denied) has a distinct test fixture and test case.
3. All dynamic states (loading, empty, error, success) tested with behavioral assertions (not only snapshots).
4. Error state tests assert recovery action is present and functional.
5. API mocks use MSW with contract-aligned fixtures; no hand-crafted response objects.
6. All async assertions use `findBy`/`waitFor`; no `setTimeout` in tests.
7. Accessible queries used (`getByRole`, `getByLabelText`); no CSS class selectors.
8. jest-axe assertion on every component render that includes interactive elements.
9. MSW `resetHandlers()` called in `afterEach` to prevent test pollution.
10. Tests survive harmless refactors (renamed CSS classes, extracted sub-components, renamed state variables).

# Used By

- frontend-change-builder
- quality-test-gate

# Handoff

Hand off to `e2e-testing` for complete browser journey validation; `contract-testing` for API mock contract alignment; `accessibility-testing` for comprehensive WCAG audit; `quality-test-gate` for coverage and pass/fail gate review.

# Completion Criteria

The capability is complete when **frontend tests prove user-visible behavior across role variants, dynamic states, and error recovery using accessible queries and contract-aligned API mocks** — with no CSS-class-based selectors, no permission gaps, no `setTimeout` flakes, and no unasserted error states.
