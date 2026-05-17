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

*Compiled from foundation capability `solution-optimality-evaluation`. Apply to every frontend change that touches a rendering path, state model, data-fetching strategy, or user-interaction critical path.*

**Three-Challenge Rule** — answer all three before finalizing any frontend design:
1. **Why this approach?** State the concrete reason (not "it felt right" or "it's the common pattern").
2. **Is this the simplest sufficient design?** Local `useState` before context; context before a global store; plain `fetch` before a caching library. Use the simplest layer that satisfies the requirement.
3. **What is the strongest alternative, and why is it rejected?** Name it. Reject it with a specific cost ("adds 180ms INP regression", "requires prop drilling 4 levels", "bundle adds 120KB gzipped").

**Performance Dimension Checklist** — evaluate each or declare N/A with a one-line rationale:

| Dimension | Required Question | Frontend-Specific Failure Mode |
|---|---|---|
| **CPU** | Is there expensive computation on the main thread (sorting, filtering, transforming large arrays) that should be memoized or moved to a Web Worker? Is a component re-rendering unnecessarily on every parent update? | Heavy sort/filter in render function without `useMemo`; entire component tree re-renders on unrelated state change |
| **Memory** | Are event listeners removed on component unmount? Are timers cleared? Is a subscription unsubscribed? Are refs to large objects cleared when no longer needed? | `addEventListener` without `removeEventListener` on unmount accumulates across route changes; `setInterval` not cleared leaks indefinitely |
| **Network** | How many API calls does this user action trigger? Is the response payload bounded (pagination, field projection)? Is stale-while-revalidate used to avoid waterfall fetching? Are assets code-split so unused routes don't block initial load? | Sequential fetch waterfall instead of parallel; unpaginated list endpoint returning 10,000 records; entire app bundle blocking initial render |
| **Disk** | Is `localStorage` / `IndexedDB` usage bounded? Are large assets (images, fonts) cached with appropriate cache headers? Is the service worker cache strategy correct for offline use? | `localStorage` growing unbounded; large images served without CDN caching; service worker caching stale API responses indefinitely |
| **Locks / Contention** | Are concurrent React state updates batched correctly (React 18 automatic batching)? Is a race condition possible between two async operations updating the same state (last-write-wins problem)? | Two in-flight fetch requests resolve out of order — stale response overwrites fresh response; non-batched state updates cause multiple re-renders per event |
| **TPS / QPS** | How many API requests does this feature generate per second at peak usage? Is there debounce or throttle on search input, scroll handlers, or resize handlers? | Unbounced search input fires a request on every keystroke; scroll handler fires 60×/s without throttle |
| **Parallelism** | Are independent API calls fetched in parallel (`Promise.all`) rather than sequentially? | Sequential `await fetch(a); await fetch(b)` adds both latencies instead of running in parallel |
| **Concurrency** | Is the component's async state transition safe if the user navigates away before the request completes? Is an in-flight request cancel handled (AbortController)? | State update on an unmounted component; stale closure captures outdated value after re-render |
| **Response Latency** | Do Core Web Vitals meet budget on a simulated median-device profile (Lighthouse 4× CPU slowdown, simulated 4G)? Does the interaction meet INP < 200ms? Is the critical render path (LCP element) above the fold and not render-blocked? | LCP element loaded lazily; render-blocking CSS or synchronous JS in `<head>`; INP > 200ms due to long task on click handler |
| **Rendering Speed** | Is main thread work per task < 50ms (Long Tasks)? Are expensive child components wrapped in `React.memo` / `v-memo`? Is layout thrashing (read offsetWidth then write style in a loop) prevented? | Synchronous style reads and writes in a loop force repeated layout recalculations; missing memoization causes 200-node subtree re-render on text input |

**Additional Professional Considerations for Frontend Code:**
- **Bundle size discipline**: `main.js` ≤ 150KB gzipped; per-route chunk ≤ 50KB gzipped. Use Webpack Bundle Analyzer or `bundlesize` to enforce this in CI — not as a manual review step.
- **DevTools verification required for critical paths**: For any component on the LCP path or interaction path, run Chrome DevTools Performance tab and Lighthouse before submitting for review. "It feels fast" is not evidence.
- **Re-render cost audit**: Use React DevTools Profiler or Vue DevTools to confirm that state updates do not cascade through unrelated component subtrees. Memoization without measurement is noise; memoization with measurement is optimization.
- **Memory leak patterns**: Route change without cleanup, global event bus without unsubscribe, third-party SDK that retains DOM references, and Web Sockets not closed on unmount are the four most common frontend memory leak sources.
- **Core Web Vitals are not optional**: LCP < 2.5s, INP < 200ms, CLS < 0.1 measured at P75 on field data. These affect SEO ranking and user retention. Lighthouse lab measurements are a minimum bar, not a final validation.

## Risk Escalation Rules
- Escalate when the change implements or modifies authentication flow, session management, or permission-restricted access — frontend auth bugs have direct security impact.
- Escalate when the change handles payment input, card numbers, or financial data — use iframe-isolated third-party payment components; never handle raw card data in application code.
- Escalate when destructive actions (delete, revoke, archive) lack confirmation dialogs with specific consequence communication.
- Escalate when sensitive data (PII, medical, financial records) is rendered in the UI — ensure the data is not logged, stored in browser storage, or exposed in DOM attributes.
- Escalate when third-party scripts are being added — CSP and Subresource Integrity review required.
- Escalate when a change affects high-traffic pages that would significantly impact Core Web Vitals scores.
- Escalate when `innerHTML`, `dangerouslySetInnerHTML`, or `eval()` are being used with any user-controlled or API-sourced content.
- Escalate when a frontend change would expose internal API structure, error details, or stack traces to the browser console or network response.

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

## Handoff
- **experience-impact-modeler** — if UX states or user flows are underspecified before implementation begins.
- **data-api-contract-changer** — when frontend changes depend on new or modified API contracts.
- **security-privacy-gate** — for auth flow changes, sensitive data rendering, or third-party script additions.
- **quality-test-gate** — for E2E test design, accessibility audit requirements, and visual regression strategy.
- **reliability-observability-gate** — when frontend changes affect client-side error tracking, performance monitoring, or SLO measurement.

## Completion Criteria
Frontend work is ready for merge when all required states are implemented, WCAG 2.1 AA requirements are met, user-generated content is sanitized, API errors produce actionable feedback, focus management is correct, authorization is enforced server-side, tests cover user behavior and accessibility, and no bundle size regression is introduced without explicit justification.
