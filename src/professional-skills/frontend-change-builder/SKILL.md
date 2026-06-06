---
name: frontend-change-builder
description: Guides product-grade frontend changes across component boundaries, routing, state management, forms, accessibility, API error handling, performance, browser behavior, frontend security, and regression verification.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Frontend Change Builder

## Mission
Implement or review product-grade frontend changes that are state-complete, accessible, maintainable, performant, and secure — with every interactive element specified across all required states, API failure modes handled gracefully, and regression evidence produced before handoff or release.

## When To Use
- Implementing or reviewing UI components, pages, or route-level screens.
- Adding or modifying form behavior, validation, or submission flows.
- Changing client-side routing, navigation guards, or page transitions.
- Modifying application state (local, global, server cache, or URL state).
- Adding or changing API data fetching, error handling, or cache invalidation.
- Implementing accessible interactions, keyboard behavior, or focus management.
- Changing frontend security boundaries: output encoding, content security policy, third-party script integration.
- Adding or modifying web performance-critical paths: rendering strategy, code splitting, asset loading.
- Agent-assisted frontend fixes need validation evidence, same-pattern scan, or placement rationale for components, hooks, state, routes, or utilities.

## Do Not Use When
- The change is purely backend, data-layer, or documentation with no user-facing or client-side behavior.
- The change is a design system contribution with no product behavior — use the design system's own contribution process.

## Non-Negotiable Rules
- **Respect existing design system and component boundaries**: do not create new components that duplicate existing ones; do not override design system tokens in one-off local styles.
- **Cover all required states for every interactive element**: loading, empty, error, success, disabled, validation, and permission-denied — omitting these creates broken flows in production.
- **Keyboard navigation and screen reader access are mandatory**: every interactive element must be keyboard-operable and have an accessible name; WCAG 2.1 AA is the minimum standard.
- **Do not place authorization or critical validation only in the client**: client-side guards are UX conveniences — the server enforces authorization; the client reflects it.
- **Never render user-controlled content as raw HTML without sanitization**: XSS through `innerHTML`, `dangerouslySetInnerHTML`, or template literals is a critical security vulnerability.
- **API errors must produce user-visible, actionable feedback**: swallowed errors or generic "Something went wrong" without recovery path are product defects.
- **Do not store sensitive information in `localStorage` or `sessionStorage`**: authentication tokens in browser storage are accessible to any JavaScript on the page — use `httpOnly` cookies for session tokens.
- **Code splitting is required for large route-level modules**: a single bundle that blocks initial page rendering is a Core Web Vitals failure.
- **Plan frontend implementation structure before adding code**: inspect existing components, hooks, routes, state stores, API clients, validators, and helpers before creating new ones; feature-local code stays local unless shared ownership is real.
- **Agent frontend fixes require execution discipline**: no local UI or state fix is accepted without scan evidence for the same component/hook pattern and validation through appropriate tests or manual artifacts.

## Industry Benchmarks
- **WCAG 2.1 / 2.2 (W3C)**: Web Content Accessibility Guidelines — AA compliance is the production baseline. Every interactive element has an accessible name, is keyboard-operable, and meets contrast requirements.
- **OWASP Top 10 — A03 (Injection) / A07 (Identification and Authentication Failures)**: XSS prevention through output encoding, CSP headers, and avoiding `innerHTML` with user content. Auth token storage security.
- **Core Web Vitals (Google)**: LCP < 2.5s, CLS < 0.1, INP < 200ms. Measurable performance targets that affect SEO and user retention.
- **React / Vue / Angular Official Documentation**: Framework-idiomatic patterns for state management, side effects, routing, and component lifecycle — deviating from idiomatic patterns creates maintenance debt.
- **Testing Library Guiding Principles (Kent C. Dodds)**: Test behavior from the user's perspective, not implementation details. `getByRole`, `getByLabelText` over `getByTestId` or CSS class selectors.
- **Web Security (MDN)**: Content Security Policy, Subresource Integrity, CORS, Referrer Policy, same-origin policy. Security controls are not optional for client-side code.
- **Storybook / Chromatic**: Component-driven development with visual regression testing and accessibility story-level testing. Every component has a story for each meaningful state.

### Framework and Pattern Selection Matrix

| Concern | React (Hooks) | Vue 3 (Composition) | Angular |
|---|---|---|---|
| Global state | Zustand / Jotai / Context (scoped) | Pinia | NgRx / signals |
| Server state / cache | TanStack Query | TanStack Query / Apollo | Apollo / NgRx Effects |
| Form management | React Hook Form | VeeValidate / Formkit | Reactive Forms |
| Routing | React Router 6 | Vue Router 4 | Angular Router |
| Accessibility audit | axe-core + Testing Library | axe-core + Testing Library | axe-core + Testing Library |
| Performance monitoring | Web Vitals library + Lighthouse | Web Vitals library + Lighthouse | Angular DevTools + Lighthouse |

## Technical Selection Criteria
Evaluate every frontend change against:
- **Component ownership**: Does the change belong to an existing component? Does it respect design system tokens, variant props, and composition boundaries?
- **Routing behavior**: Are route guards, navigation redirects, and back-button behavior specified? Does the URL reflect application state?
- **State scope**: Is the state local (component), shared (context/store), or server-synchronized (query cache)? Is state scope as narrow as possible?
- **Data fetching and cache**: What is the stale-while-revalidate strategy? What happens on fetch error or network timeout? Is the loading state bounded?
- **Form validation**: Is validation on blur (field-level) or on-submit? Are error messages field-specific and actionable? Is form state preserved on error?
- **API error classification**: Does the UI differentiate between network failure (offline), server error (5xx), validation error (4xx), and auth error (401/403)?
- **Accessibility**: Does every interactive element have an accessible name? Is focus managed after route changes, modal open/close, and async operations?
- **Output encoding**: Is all user-generated content rendered through safe text rendering (`.textContent`, JSX text nodes) — never via `innerHTML` with unsanitized content?
- **Performance**: Is this component on the critical render path? Does it require code splitting, lazy loading, or server-side rendering?
- **Frontend structure**: Existing components, hooks, state stores, API clients, validators, and helpers inspected; feature-local vs. shared decision; component/hook/state/API/helper placement; new imports and dependency direction; test placement.
- **Test strategy**: Are tests written against behavior (user interactions, accessibility queries) rather than implementation details?

### Decision Tree: State Management Choice

```
Is state used in only one component?
└── Use local state (useState / ref / signal)
Is state shared between sibling components?
└── Lift to nearest common parent; if prop drilling > 2 levels, use context
Is state fetched from a server and cached?
└── Use TanStack Query (React/Vue) or Angular HttpClient with caching
Is state persisted across sessions?
└── Use httpOnly cookie (auth) or URL params (shareable view state) — not localStorage for sensitive data
Is state a complex business domain object with mutations?
└── Use a dedicated store (Zustand / Pinia / NgRx) with typed actions
```

## Solution Optimality Self-Check
Apply when the change touches a rendering path, state model, data-fetching strategy, or interaction-critical path. Answer the **Three-Challenge Rule** before finalizing: (1) why this approach over the alternatives, (2) is it the simplest sufficient layer (local state before context before a store), (3) what is the strongest alternative and the specific cost that rejects it ("adds 180ms INP", "bundle adds 120KB gzipped"). Then budget the performance dimensions — CPU, memory, network, disk, locks/contention, TPS/QPS, parallelism, concurrency, response latency, rendering speed — or mark each N/A with a one-line rationale.

Load [references/solution-optimality.md](references/solution-optimality.md) for the full frontend performance-dimension matrix and additional considerations (bundle budgets, Core Web Vitals, re-render and memory-leak audits) when the change touches a performance-sensitive path. Method compiled from `solution-optimality-evaluation`.

## Risk Escalation Rules
- Escalate when the change implements or modifies authentication flow, session management, or permission-restricted access — frontend auth bugs have direct security impact.
- Escalate when the change handles payment input, card numbers, or financial data — use iframe-isolated third-party payment components; never handle raw card data in application code.
- Escalate when destructive actions (delete, revoke, archive) lack confirmation dialogs with specific consequence communication.
- Escalate when sensitive data (PII, medical, financial records) is rendered in the UI — ensure the data is not logged, stored in browser storage, or exposed in DOM attributes.
- Escalate when third-party scripts are being added — CSP and Subresource Integrity review required.
- Escalate when a change affects high-traffic pages that would significantly impact Core Web Vitals scores.
- Escalate when `innerHTML`, `dangerouslySetInnerHTML`, or `eval()` are being used with any user-controlled or API-sourced content.
- Escalate when a frontend change would expose internal API structure, error details, or stack traces to the browser console or network response.
- Escalate to `agent-execution-discipline` when an agent closes frontend work without validation evidence, same-pattern scan, or reuse-and-placement rationale for new shared UI structure.

## Critical Details
- **XSS prevention is non-negotiable**: React JSX text nodes are auto-escaped. `dangerouslySetInnerHTML` bypasses this — use it only with content sanitized through DOMPurify. Vue's `v-html` has the same risk profile.
- **`httpOnly` cookie vs. `localStorage` for auth tokens**: `httpOnly` cookies cannot be read by JavaScript — immune to XSS token theft. `localStorage` tokens are accessible to any script on the page — do not use for session tokens.
- **Optimistic UI requires rollback**: When applying an optimistic update, maintain the previous state in case the server request fails — TanStack Query provides `onMutate` / `onError` hooks for this pattern.
- **Skeleton screen layout stability**: Skeleton screens must match the final content dimensions as closely as possible — a layout shift when content loads is a CLS failure and a disorienting user experience.
- **Event handler cleanup**: In React, `useEffect` must return a cleanup function for subscriptions, timers, or event listeners — memory leaks from uncleaned effects accumulate in SPAs.
- **`aria-live` for async updates**: When content updates asynchronously (new message, search result, notification), `aria-live="polite"` announces the change to screen reader users without interrupting their current reading flow.
- **Form autocomplete**: Payment forms should set `autocomplete="cc-number"` etc. — browser-native autocomplete reduces friction and follows PCI DSS UX guidance. Disabling autocomplete without reason degrades UX and accessibility.

### Anti-Examples

| Frontend Pattern | Problem | Corrected Approach |
|---|---|---|
| `<div dangerouslySetInnerHTML={{ __html: userInput }} />` | XSS — user input rendered as HTML | `<div>{userInput}</div>` or sanitize with DOMPurify before `dangerouslySetInnerHTML` |
| `localStorage.setItem('token', jwt)` | Token accessible to XSS scripts | `httpOnly` cookie set by server; frontend never touches the token value |
| Error handler: `catch (e) { console.log(e) }` — no UI feedback | User has no indication of failure; no recovery path | Display specific error message; provide retry or contact path |
| `onClick` button with no keyboard equivalent | Keyboard users cannot trigger action | Native `<button>` with `onClick` — native button is keyboard-operable by default |
| `useEffect(() => { fetchData() }, [])` — no cleanup, no error state | Memory leak; missing loading/error UI | Use TanStack Query or equivalent with loading, error, and success states |
| Icon-only button: `<button><TrashIcon /></button>` | No accessible name; screen reader reads nothing | `<button aria-label="Delete order #1234"><TrashIcon /></button>` |

## Failure Modes
- **Missing state coverage breaks flows**: The error state for a critical form is never implemented — users who encounter a server error see a blank form with no explanation.
- **Over-shared state causes regressions**: A global store mutation in one component inadvertently resets the state of another — cross-component state bugs are hard to isolate.
- **Client-only authorization is bypassed**: A "delete" button is hidden for read-only users in the UI but the API endpoint has no authorization check — a direct API call deletes the resource.
- **Unhandled API errors crash the page**: An unhandled Promise rejection causes an unhandled exception that crashes the React root — the entire page goes blank.
- **XSS through `innerHTML`**: User-generated content containing `<script>` tags is rendered via `innerHTML` — the script executes in the context of the origin and can exfiltrate session data.
- **Accessibility blocker on primary flow**: The checkout form's "Place Order" button has no accessible name — screen reader users cannot complete a purchase.
- **Bundle size regression**: A new dependency adds 400 KB to the initial bundle without code splitting — LCP increases by 1.5s on mobile.

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
Return a frontend implementation plan or review with:
- **Component specification**: Component hierarchy, state ownership, props interface, and design system integration.
- **State model**: State scope (local/shared/server), state machine (if applicable), and mutation patterns.
- **API integration**: Endpoint, request/response types, loading/error/success handling, and cache invalidation strategy.
- **Accessibility obligations**: Accessible names, ARIA roles, focus management, keyboard interaction, and contrast requirements.
- **Security review**: XSS prevention, token storage, CSP implications, third-party script review.
- **Performance considerations**: Code splitting, lazy loading, rendering strategy, and Core Web Vitals impact.
- **Frontend structure**: Component, hook, state, API client, route, form validator, and helper placement; feature-local vs. shared decision; reuse candidates; public/private boundary; test placement.
- **Execution discipline evidence**: Test or screenshot artifacts, command outputs, same-pattern scan, placement rationale, residual risks, and closure boundary.
- **Test strategy**: Unit tests (component behavior), integration tests (user flow), accessibility tests (axe-core), and visual regression tests.
- **Residual risks**: Known risks accepted with justification.

## Quality Gate
1. All required states (loading, empty, error, success, disabled, validation) are implemented for every interactive element.
2. WCAG 2.1 AA is satisfied: accessible names on all interactive elements, keyboard operability, sufficient color contrast.
3. User-generated and API-sourced content is never rendered via `innerHTML` without DOMPurify sanitization.
4. Authentication tokens are stored in `httpOnly` cookies — not `localStorage` or `sessionStorage`.
5. API errors produce user-visible, specific, actionable feedback — no swallowed errors.
6. Focus management is implemented for modals, route changes, and async operations.
7. Tests cover behavior from the user's perspective using accessibility queries (Testing Library).
8. No new dependencies exceed bundle size budget without code splitting.
9. Destructive actions have confirmation dialogs with consequence-specific copy.
10. Authorization is enforced server-side; client-side guards are UX-only and documented as such.
11. Existing frontend components, hooks, state stores, API clients, validators, and helpers were checked before new code was added.
12. New components and hooks have feature-local vs. shared placement rationale.
13. Feature-local state is not moved to global state without cross-feature ownership.
14. No business logic is added to shared UI, common hooks, or generic utils.
15. Agent-assisted frontend changes include evidence, same-pattern scan for local fixes, and closure package.

## Handoff
- **experience-impact-modeler** — if UX states or user flows are underspecified before implementation begins.
- **data-api-contract-changer** — when frontend changes depend on new or modified API contracts.
- **security-privacy-gate** — for auth flow changes, sensitive data rendering, or third-party script additions.
- **quality-test-gate** — for E2E test design, accessibility audit requirements, and visual regression strategy.
- **reliability-observability-gate** — when frontend changes affect client-side error tracking, performance monitoring, or SLO measurement.
- **agent-execution-discipline** — when frontend validation evidence, same-pattern scan, placement rationale, or handoff boundary is missing.

## Completion Criteria
Frontend work is ready for merge when all required states are implemented, WCAG 2.1 AA requirements are met, user-generated content is sanitized, API errors produce actionable feedback, focus management is correct, authorization is enforced server-side, tests cover user behavior and accessibility, no bundle size regression is introduced without explicit justification, and the frontend structure plan confirms component/hook/state/API/helper placement, feature-local vs. shared decisions, reuse candidates, public/private boundary, and test placement.
