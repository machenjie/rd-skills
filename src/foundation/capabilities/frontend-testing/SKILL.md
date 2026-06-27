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

# Stage Fit

Owns frontend test-design and review when a user-facing surface, component tree, route, API state, permission branch, or accessibility behavior needs executable proof. Use during planning, coding, debugging, bug-fix repair, code-review, testing, release, and handoff when frontend test evidence must prove visible behavior rather than component internals. In planning, it turns behavior and state obligations into component/integration/E2E boundaries. In review, it rejects tests that pass through implementation details while missing user-visible outcomes, role variants, recovery actions, accessibility semantics, or contract-aligned API fixtures. Repository graph, project memory, and execution trajectory can locate prior frontend test patterns, but current source, stories, tests, API schemas, and validation output must confirm that a pattern is still authoritative.

# Non-Negotiable Rules

- **Test user-observable behavior, not implementation structure.** Assertions must target what users see and can do: rendered text, visible buttons, form fields, navigation links, accessible labels, validation messages. Do not assert: component state variable names, internal function call counts, CSS class names (unless they encode semantic meaning), or React prop values that are not reflected in the DOM.
- **Use accessible queries.** Testing Library query priority: `getByRole` (first choice for interactive elements), `getByLabelText` (forms), `getByPlaceholderText` (when label unavailable), `getByText`, `getByDisplayValue`, `getByAltText`, `getByTitle`; use `getByTestId` only as last resort and only with `data-testid` attributes (never CSS class or element selectors). Never use `querySelector('.btn-primary')` — brittle; breaks on style refactor.
- **Every permission state must have a test fixture.** If a component renders differently for admin vs member vs viewer roles, each role must have a test case. Do not test only the highest-privilege view and assume lower privilege works.
- **API mocks must match the contract.** Mocked API responses must be consistent with the dto-schema / OpenAPI contract. Use contract-aligned fixtures, not hand-crafted objects. A mock that diverges from the real response shape creates a false safety net — tests pass, production fails.
- **Error and empty states must be tested for recovery.** Testing an error state means: (1) render the error state; (2) assert the error message is visible and correct; (3) assert the recovery action (retry button, back link) is present and functional. Snapshotting an error state without asserting recovery action is incomplete.
- **Loading states must not cause test flakiness.** Do not `await` arbitrary timeouts to wait for async behavior. Use `await screen.findByText(...)` (waits for element to appear) or `waitFor(() => expect(...))`. Never use `await new Promise(resolve => setTimeout(resolve, 500))` in tests.
- **Coverage targets are secondary to behavior completeness.** A 95% line coverage achieved by testing `getProps()` methods is not better than 70% coverage that tests all critical user flows. Coverage is a floor signal, not a quality signal. What matters: are the user journeys and risk states covered?

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Component behavior proof | Component/view output, interaction, form, or local state changes. | Assert accessible user-visible behavior and recovery, not props or internals. | Render boundary, user action, visible result, query strategy, negative/recovery case. | `interaction-state-modeling`, `unit-testing` | CSS selectors, snapshots-only tests, private helper assertions. |
| API-backed state test | Loading, stale, timeout, optimistic, error, pagination, or response-shape behavior appears in UI. | Prove request lifecycle states through contract-aligned fixtures and deterministic async handling. | API schema/fixture source, MSW/reset policy, state coverage, timeout/rollback assertion. | `frontend-api-integration`, `contract-testing` | Hand-crafted DTO mocks or fetch-client module mocks by default. |
| Permission and role matrix | Role, ownership, feature flag, tenant, unauthenticated, or permission-denied branch changes UI. | Prove allowed and denied visible outcomes without leaking restricted state. | Role fixtures, denied branch, accessible disabled/denied treatment, security review handoff. | `permission-boundary-modeling`, `security-privacy-gate` when sensitive | Highest-privilege-only tests. |
| Accessibility interaction | Modal, menu, form error, disabled action, live update, keyboard path, or focus change. | Verify name/role/value, focus movement, keyboard behavior, ARIA live/error announcements. | Accessibility queries, keyboard sequence, axe/jest-axe output, focus assertion. | `design-system-rules`, `interaction-state-modeling` | Accessibility as a visual snapshot. |
| Journey boundary decision | Behavior spans multiple components, routes, services, or durable side effects. | Choose component integration vs narrow E2E and avoid duplicating lower-level coverage. | User flow, side effect, risk level, omitted levels with residual risk. | `test-strategy`, `e2e-testing`, `quality-test-gate` | E2E for every field variant. |

# Industry Benchmarks

Anchor against Testing Library accessible-query guidance, user-event realism, MSW contract-aligned network mocks, Vitest/Jest deterministic runners, Storybook interaction and visual checks, axe-core/WCAG 2.2 accessibility assertions, and Testing Trophy layer selection. Keep the body focused on selection and evidence rules; load the benchmark reference for detailed test-level matrices, state checklists, and mock alignment examples.

# Selection Rules

Select this capability when **frontend component and integration testing strategy** is the primary design concern. Adjacent routing:

- Prefer `e2e-testing` when complete browser journeys spanning multiple pages and services need to be validated.
- Prefer `unit-testing` when the test subject is a pure logic function with no DOM or component behavior.
- Prefer `contract-testing` when the primary risk is API response shape divergence between frontend mock and backend implementation.
- Prefer `quality-test-gate` when a comprehensive WCAG audit across the full application is required.

# Risk Escalation Rules

Escalate when the change touches: authentication or authorization flows (login, token refresh, permission gates); payment or checkout UI; destructive actions (delete account, bulk delete, data export); accessibility-critical interactions in regulated (WCAG AA required) products; cross-browser behavior differences (use E2E for these); or features with contractual SLAs on uptime.

# Proactive Professional Triggers

- **Signal:** A frontend test asserts CSS classes, component props, private state, hook calls, or snapshots without behavior assertions. **Hidden risk:** tests pass while the user-visible experience regresses. **Required professional action:** rewrite around accessible user behavior and state what refactors the test should survive. **Route to:** `frontend-testing`, `code-clarity-maintainability`. **Evidence required:** public behavior assertion, rejected implementation selector, and validation output.
- **Signal:** API-backed UI tests handcraft response objects or mock the HTTP client module. **Hidden risk:** fixtures drift from DTO/OpenAPI/schema and production crashes are hidden. **Required professional action:** use MSW or equivalent contract-aligned fixtures and reset handlers. **Route to:** `frontend-api-integration`, `contract-testing`. **Evidence required:** fixture source, schema/type alignment, handler reset policy, malformed-response case.
- **Signal:** Role, tenant, ownership, or permission behavior has only admin/happy-path coverage. **Hidden risk:** denied states, disabled affordances, and data-leak branches are untested. **Required professional action:** build role fixtures and include allowed, denied, unauthenticated, and non-leaking assertions. **Route to:** `permission-boundary-modeling`, `security-privacy-gate` when sensitive. **Evidence required:** role matrix, denied assertion, accessible denial/disabled state.
- **Signal:** Error, empty, timeout, optimistic rollback, or stale state is represented only by a snapshot. **Hidden risk:** users lose recovery, see misleading completion, or cannot retry. **Required professional action:** assert recovery actions, preserved input, rollback behavior, and ARIA/live-region status. **Route to:** `interaction-state-modeling`, `quality-test-gate`. **Evidence required:** state coverage map, user action, recovery assertion, accessibility assertion.
- **Signal:** A prior test pattern is selected from project memory, repository graph proximity, or an earlier agent trajectory. **Hidden risk:** stale patterns or unreviewed repair paths become copied test debt. **Required professional action:** confirm against current source/tests/stories/schemas and validation freshness before reusing. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, freshness limits, accepted/rejected pattern, and command outcome.

# Critical Details

Frontend tests fail for the wrong reasons when anchored to implementation. Precision failures:

- **Snapshot test false safety.** Snapshot test of the error state captures: `<p className="error-msg">Something went wrong</p>`. The snapshot is "passing." But the retry button that was present 2 weeks ago was removed in an unrelated refactor. The snapshot does not include the retry button. Test still passes. User cannot recover from errors. Snapshot tests must be supplemented with explicit behavioral assertions.
- **`getByTestId` as first choice.** A test uses `getByTestId('submit-btn')` on every button. The submit button label changes from "Submit" to "Place Order" — a legitimate UX improvement. The `data-testid` is unchanged. Test passes. But the user-visible label change was never verified. Use `getByRole('button', { name: 'Place Order' })` — tests both presence and accessible label.
- **Role fixture gap.** Tests use an admin user fixture for all component tests. The component has a permission check: `if (user.role === 'admin') show delete button`. Tests always show the delete button. A viewer accesses the same component via a URL manipulation — delete button renders for viewer. No test caught this.
- **Async `waitFor` with arbitrary timeout.** `await new Promise(resolve => setTimeout(resolve, 500))` in a test. This is a flake generator: on fast CI it passes; on slow CI it times out before the element appears. Use `await screen.findByText('Success')` which retries until the element appears or the default timeout (1000ms) expires.
- **MSW not reset between tests.** Test A registers an MSW handler returning a 500 error. Test B does not reset handlers. Test B inherits the 500 handler. Test B fails with an unexpected API error. Always call `server.resetHandlers()` in `afterEach`.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 frontend test selection and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete frontend test plan, when role/state/accessibility/API mock coverage is uncertain, or before implementation starts. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when test-level selection, state coverage detail, or mock alignment examples are needed. Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on repository graph, project memory, execution trajectory, validation freshness, tool permission boundaries, or a changed-behavior-to-test map. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load these references for pure routing or trivial wording work where the output contract and quality gate are enough.

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

- **Snapshot-only error state:** snapshot test passes after a retry button is removed in a refactor; users cannot recover from errors in production.
- **Happy-path permission gap:** only admin behavior is tested; permission-denied view shows admin content to a viewer, and the bypass is discovered in a pentest.
- **Contract-drifting mock:** hand-crafted API mock omits required `role`; component crashes in production on `user.role.toUpperCase()` while tests stay green.
- **Arbitrary async wait:** `setTimeout(500)` causes 1 in 10 CI runs to fail; PRs block on flake investigation instead of behavior evidence.
- **MSW handler pollution:** a 500 handler leaks into later tests; suite passes in isolation but fails 30% of the time in full CI.
- **CSS selector coupling:** class-based selectors break when the design system moves from BEM to CSS Modules; 200 tests fail without any user-visible regression.
- **Keyboard path blind spot:** modal tab order breaks because no keyboard navigation test exists; WCAG 2.4.3 failure appears during audit.
- **Accessibility assertion gap:** no axe-core or label assertion catches a mismatched `for` / `id`; screen reader users cannot identify field purpose.
- **Stale memory copied as coverage:** an old story or prior test pattern is reused after the component contract changed; the selected test never covers the current denied state.
- **Stale validation evidence:** test output predates the final fixture or MSW handler edit; handoff claims behavior coverage for a state no current test exercises.

# Output Contract

Return a frontend test plan with:

- `mode_selected` (component behavior proof / API-backed state test / permission-role matrix / accessibility interaction / journey boundary decision)
- `behavior_scope` (surface, user goal, changed visible behavior, affected route/component/story, and current source/test evidence)
- `source_evidence` (current tests, stories, schemas, API mocks, repository graph, project memory, or execution trajectory inspected with freshness limits)
- `test_level_decision` (unit/component integration/E2E/visual/a11y level chosen, omitted levels, residual risk, and rationale)
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
- `changed_behavior_to_test_map` (each visible behavior, state, role, API condition, or a11y obligation mapped to a test or explicit residual risk)
- `handoff_boundaries` (what belongs to unit, E2E, contract, API integration, state modeling, design-system review, or quality gate)
- `evidence_limits` (what the selected tests prove and do not prove about browsers, backend contracts, real devices, production data, and untested journeys)

# Evidence Contract

Close a frontend-testing change only when the output names:

- **Boundaries inspected:** component/route/story source, current tests, API schema or fixture source, role/permission model, accessibility surface, repository graph, project memory, and execution trajectory accepted, rejected, stale, or not verified.
- **Behavior-to-test map:** every changed visible behavior, role branch, state transition, API condition, keyboard/focus path, and recovery action mapped to a component, integration, E2E, visual, accessibility, or contract test.
- **Validation evidence:** command, working directory, exit code or outcome, report/artifact path, and freshness after the final material edit.
- **What evidence proves:** the exact visible behavior, state, permission branch, API mock contract, query strategy, flake control, or accessibility obligation covered.
- **What evidence does not prove:** untested browsers/devices, backend contract enforcement, production data, real assistive technology behavior, visual regressions, or journeys outside the selected level.
- **Residual risk and handoff:** accepted gaps, owner, review date or reopen trigger, and next gate such as `frontend-api-integration`, `contract-testing`, `e2e-testing`, or `quality-test-gate`.

A coverage percentage, snapshot update, or "test the component" statement is not sufficient evidence.

# Benchmark Coverage

Behavior improvement should be validated structurally: weak frontend test plans usually assert implementation details, use admin-only fixtures, handcraft API mocks, snapshot error states, skip keyboard/focus assertions, or use arbitrary waits. Improved outputs must name mode, user-visible behavior, state/role coverage, contract-aligned fixture source, accessible query strategy, flake controls, validation evidence, and handoff boundaries while keeping detailed benchmark examples in references.

# Routing Coverage

Route here when the primary work is frontend component, route, or page-level test design for user-visible behavior. Guard against over-routing by handing off when the primary work is pure logic (`unit-testing`), full browser journeys (`e2e-testing`), API schema compatibility (`contract-testing`), request lifecycle behavior (`frontend-api-integration`), UI state specification (`interaction-state-modeling`), or overall risk-layer selection (`test-strategy` / `quality-test-gate`).

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
11. Selected mode, behavior scope, and test-level rationale are explicit.
12. Project memory, repository graph, and execution trajectory evidence are source-confirmed or marked not verified.
13. Each changed visible behavior maps to a test, validator, or named residual risk.
14. Handoff boundaries and evidence limits are named so frontend tests are not over-claimed as full contract, browser, device, or production proof.

# Used By

- frontend-change-builder
- quality-test-gate

# Handoff

Hand off to `unit-testing` for pure logic; `e2e-testing` for complete browser journey validation; `contract-testing` for API mock contract alignment; `frontend-api-integration` for request lifecycle behavior; `interaction-state-modeling` for state-matrix gaps; `design-system-rules` for component semantics; and `quality-test-gate` for comprehensive WCAG audit, coverage, and pass/fail gate review.

# Completion Criteria

The capability is complete when **frontend tests prove user-visible behavior across role variants, dynamic states, and error recovery using accessible queries and contract-aligned API mocks** — with no CSS-class-based selectors, no permission gaps, no `setTimeout` flakes, and no unasserted error states.
