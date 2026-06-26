---
name: frontend-api-integration
description: Designs frontend API integration for timeout, cancellation, retries, auth expiry, pagination, stale data, error mapping, and response shape validation.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "35"
changeforge_version: 0.1.0
---

# Mission

Design frontend API integration so user-facing views remain **provably correct across latency, cancellation, token expiry, pagination instability, stale data, malformed responses, and network failure** — with explicit request lifecycle contracts, bounded retry policies, and user-actionable error recovery for every operation class.

# When To Use

Use this capability when a frontend change: fetches or mutates data from any API endpoint; adds loading, empty, error, or stale states to a view; introduces optimistic UI updates; implements pagination (cursor, offset, or infinite scroll); handles authentication token refresh; retries failed requests; cancels in-flight requests on navigation; validates response shape at the client boundary; or integrates with a third-party API.

# Do Not Use When

Do not use this capability to define the server-side endpoint contract (use `api-contract-design`), to design form submission lifecycle (use `form-validation-design`), or to design client-side state ownership and invalidation strategy (use `state-management-design`).

# Stage Fit

Use during experience-definition, implementation-planning, coding, review, and testing when a frontend surface depends on API data, request cancellation, cache freshness, response validation, auth expiry, retries, pagination, optimistic updates, or user-visible API error recovery. In planning, define the operation lifecycle, source evidence, stale-response controls, error mapping, and tests before implementation. In coding/review, reject stale project-memory or repository-graph claims unless current source, API contracts, mocks, and validation output confirm the integration behavior. Hand off when the primary question is server contract design, form submission authority, state ownership, or full frontend test strategy.

# Non-Negotiable Rules

- **Every request must have a defined cancellation point.** When a user navigates away from a view while a request is in flight, the request must be cancelled using `AbortController`. Without cancellation: stale responses can overwrite newer state; memory leaks occur in SPA frameworks when state is updated after component unmount; multiple in-flight requests for the same resource create race conditions.
- **Retries are only safe for idempotent operations.** GET and HEAD requests may be retried unconditionally. POST, PUT, PATCH, DELETE mutations must not be retried unless: (1) the server returns a `Retry-After` header (transient 429/503), AND (2) the request includes an `Idempotency-Key` header that prevents duplicate effects on the server. Never retry a mutation silently on timeout — the operation state is unknown; the server may have committed it.
- **Response shape must be validated at the client boundary.** The frontend must not destructure or render API responses without validating the shape. Use a schema validation library (Zod, Valibot, Yup). Invalid/unexpected shapes must produce a specific "unexpected response" error state, not a JavaScript TypeError crash in the render tree.
- **Authentication expiry must never produce a broken page.** When a 401 Unauthorized response is received: attempt token refresh exactly once; if refresh succeeds, replay the original request; if refresh fails, redirect to login with the current URL as `next` parameter for post-login redirect; never display a raw 401 error to the user.
- **Optimistic updates must have a rollback path.** Any optimistic state mutation must store the previous state before applying the optimistic update. On server error, revert to the previous state and show an error notification. Without rollback, failed optimistic updates leave the UI in a permanently incorrect state.
- **Error messages must be user-actionable.** Map API error responses to user-facing messages before display. Never expose: HTTP status codes as user messages; internal error codes, stack traces, or exception class names; SQL or schema details. User message must identify what went wrong and what the user can do next (retry, contact support, check inputs).
- **Pagination must handle instability.** Cursor-based pagination is preferred over offset for any list that can be mutated. Offset pagination on mutable data: newly inserted records shift pages (records duplicated across pages); deleted records collapse pages (records skipped). When offset pagination is required for legacy reasons, document the instability and add a "new items may not appear immediately" UX disclosure.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Read lifecycle | Page/view/query fetch, search, refresh, or background revalidation. | Cancellation, timeout, stale response rejection, cache key, and recovery. | Operation list, current API client/cache pattern, AbortController or ignore policy, stale test obligation. | `interaction-state-modeling`, `frontend-testing` | Mutation idempotency design unless writes exist. |
| Mutation lifecycle | Create/update/delete/import/export action, optimistic UI, duplicate-submit risk, or unknown timeout outcome. | Idempotency, rollback, conflict mapping, durable confirmation, and unsafe retry prevention. | Operation side effect, idempotency key requirement, rollback state, timeout language, retry stop condition. | `idempotency-retry-design`, `state-management-design` | Silent retry on timeout. |
| Auth and permission API state | 401, refresh token, session expiry, permission change, 403/404 posture, or sign-in redirect. | Refresh-once, cache clearing, no loops, non-leaking denied state. | Auth source, refresh max attempts, redirect target, protected cache invalidation, denied-path map. | `security-privacy-gate`, `error-code-design` | Raw 401/403 display. |
| Response contract and errors | DTO/schema change, problem details, violations, malformed data, provider errors, or client crash risk. | Shape validation, stable error taxonomy, safe user recovery, diagnostic separation. | Schema source, field/error map, invalid-shape behavior, safe telemetry rule. | `api-contract-design`, `error-code-design`, `dto-schema-design` | Destructuring unvalidated JSON. |
| Pagination and cache freshness | Cursor/offset/keyset list, infinite scroll, stale data, mutation invalidation, or focus/reconnect refresh. | Stable ordering, cache ownership, invalidation triggers, empty/end states, stale presentation. | Pagination contract, sort/tiebreaker, cache key, invalidation map, stale/empty behavior. | `state-management-design`, `frontend-testing` | Offset instability without disclosure. |
| Third-party or browser trust boundary | Browser calls external API, token-bearing requests, PII/error telemetry, CSP/connect-src, or untrusted response. | Exposed credential prevention, allowed destinations, response validation, redaction. | Destination allowlist, token location, log redaction, CSP/connect-src or equivalent control. | `security-privacy-gate`, `threat-modeling` | Shipping provider credentials to browser. |

# Industry Benchmarks

Anchor against Fetch API and AbortController, TanStack Query, SWR, Axios AbortController support, RFC 7807/RFC 9457 Problem Details, RFC 5861 stale-while-revalidate, idempotency-key practice, exponential backoff with jitter, Relay cursor pagination, OpenTelemetry TraceContext, CSP `connect-src`, OWASP API security guidance, and contract-aligned network mocking. Keep this body focused on routing, lifecycle decisions, evidence, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed benchmark anchors, lifecycle/retry/error/pagination/cache matrices, race/freshness controls, graph/memory/trajectory coupling, and anti-pattern review.

# Selection Rules

Select this capability when **frontend data fetching and request lifecycle** are the primary design concern. Adjacent routing:

- Prefer `form-validation-design` when the primary concern is form field validation, submission state machine, and duplicate-submit protection.
- Prefer `api-contract-design` when the primary concern is the server-side API contract (endpoint definitions, request/response schemas).
- Prefer `state-management-design` when the primary concern is client-side state ownership, derived state, and cross-component cache invalidation.
- Prefer `idempotency-retry-design` when the primary concern is server-side deduplication implementation for retried mutations.

# Proactive Professional Triggers

- **Signal:** a request lifecycle is described as "fetch data and show errors" without operation list, cancellation trigger, timeout, or stale-response rule. **Hidden risk:** implementers create inconsistent loading/error behavior and stale responses overwrite current state. **Required professional action:** require operation-level lifecycle and stale-response controls. **Route to:** `interaction-state-modeling`, `frontend-testing`. **Evidence required:** operation list, current input/cache key, cancellation or ignore rule, and stale-response test.
- **Signal:** a mutation has retry, timeout, optimistic update, or duplicate-submit behavior but no idempotency key or rollback contract. **Hidden risk:** duplicate side effects, false success, or permanent UI/server divergence. **Required professional action:** require mutation retry/idempotency and rollback map. **Route to:** `idempotency-retry-design`, `state-management-design`. **Evidence required:** idempotency requirement, timeout unknown-outcome language, pre-mutation state, conflict/rollback test.
- **Signal:** 401, token refresh, role change, or permission-denied behavior is handled by a generic error state. **Hidden risk:** refresh loop, stale protected cache, leaking resource existence, or broken login recovery. **Required professional action:** define refresh-once, cache clear, sign-in redirect, 403/404 posture, and denied UI state. **Route to:** `security-privacy-gate`, `error-code-design`. **Evidence required:** auth flow, max refresh attempts, protected cache invalidation, denied-path test.
- **Signal:** API responses are trusted because TypeScript types, generated clients, or prior mocks exist. **Hidden risk:** malformed or version-skewed JSON crashes the render tree. **Required professional action:** validate at the runtime boundary and test malformed responses. **Route to:** `api-contract-design`, `frontend-testing`. **Evidence required:** schema source, runtime parse/guard behavior, invalid-shape state, mock/fixture contract alignment.
- **Signal:** project memory, repository graph, or earlier trajectory says an API client, cache key, or mock pattern already exists. **Hidden risk:** stale integration pattern is copied after API schema, auth, cache, or test conventions changed. **Required professional action:** confirm current source, schema, mocks, tests, and validation freshness before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected pattern, freshness limit, and validation command or residual risk.

# Risk Escalation Rules

Escalate when: a mutation request handles payment, order creation, account deletion, or bulk data modification; authentication token storage or refresh logic is being introduced or changed (XSS attack surface); a third-party API call exposes credentials to the browser; an API response contains PII and is being logged or cached without redaction; optimistic updates are applied to financial or inventory data.

# Critical Details

Frontend API integration fails silently when assumptions about network conditions are not codified. Precision failures:

- **Race condition: last-write-wins on concurrent fetches.** User types in a search box; request A fires for "ali", request B fires for "alice". Response B arrives first (faster query), response A arrives second. UI renders results for "ali" instead of "alice". Fix: cancel request A when request B fires using AbortController; accept only the response matching the current input value.
- **Token refresh loop.** A 401 triggers a token refresh. The refresh also fails with 401. The code retries the refresh. Infinite loop. Token refresh must be attempted exactly once. On refresh failure: stop, clear session, redirect to login. Never retry a failed refresh.
- **Optimistic update not rolled back.** User marks a task complete (optimistic UI: task immediately disappears from list). Server returns 500. The task is gone from the UI but not from the database. User thinks the task is complete. Fix: store pre-mutation state; on error, revert and show error toast.
- **Undefined field access on unexpected response.** API temporarily returns `{"items": null}` instead of `{"items": []}`. Frontend renders `items.map(...)`, causing `TypeError: Cannot read properties of null`. Zod validation at the boundary converts this to an explicit "unexpected response" error state before the render tree sees the data.
- **Exposing auth token in error log.** Request fails; error handler logs `console.error("Request failed", config)`. `config` includes `Authorization: Bearer <token>`. Token is now in browser console history and any error monitoring tool that collects console logs. Sanitize request config before logging; never log Authorization headers.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| No AbortController on navigation | Stale response updates state after user has navigated away; wrong data displayed |
| Retry POST mutation on network error | Duplicate order created; customer charged twice |
| `response.data.user.profile.name` with no shape validation | Crashes on any API schema change; TypeError in production |
| 401 triggers infinite token refresh loop | App hangs; user never redirected to login |
| Optimistic update with no rollback | Failed mutation leaves UI permanently out of sync with server |
| `Authorization: Bearer ...` logged in error handler | Token exposed in monitoring tools; security incident |
| Offset pagination on append-heavy feed | Duplicate or skipped items as user pages; data integrity UX failure |
| Fetch without timeout | Request hangs indefinitely on backend issue; loading spinner never resolves |

# Failure Modes

- Search results race: user sees stale "ali" results while "alice" query was faster; no cancellation; UX incorrect.
- Mutation retry without idempotency: double order creation on slow connection retry; customer charged twice; refund required.
- Token refresh loop on 401 cascade: infinite retry; app becomes unresponsive; user unable to log in or out.
- Undefined property access on API change: `TypeError` uncaught; white screen in production; no error boundary; users see blank page.
- Optimistic delete not rolled back: item appears deleted in UI; server returned 500; item still exists; user confused; support ticket.
- Auth token in Sentry/Datadog error: full `Authorization` header logged; token harvested from monitoring tool; account takeover.
- Offset pagination on mutating list: user pages through 200-item list; 10 items inserted during session; items 190-200 duplicated on page 20 and page 21.
- No timeout on third-party API: payment gateway goes down; frontend request hangs for 60+ seconds; entire checkout flow blocked.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 frontend API integration routing, lifecycle, evidence, output, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete API-backed UI operation, request lifecycle, retry policy, auth expiry behavior, cache invalidation rule, error mapping, pagination behavior, optimistic update, or test obligation. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when detailed benchmark anchors, lifecycle/retry/cache/error matrices, race/freshness controls, graph/memory/trajectory coupling, or anti-pattern review is needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or minor wording work where the inline output contract and quality gate are enough.

# Output Contract

Return a frontend API integration plan with:

- `mode_selected` (read lifecycle / mutation lifecycle / auth and permission API state / response contract and errors / pagination and cache freshness / third-party or browser trust boundary)
- `source_evidence` (current API client, hooks, route/component source, generated client, OpenAPI/DTO/schema, mocks, stories, tests, repository graph, project memory, or execution trajectory inspected with freshness limits)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for each reused API client, cache key, mock fixture, retry wrapper, auth handler, pagination pattern, or test pattern)
- `operations` (name, HTTP method, endpoint, purpose, mutating/read, optimistic update?)
- `request_lifecycle` (per operation: AbortController or equivalent, timeout, cancellation trigger, stale-response discard rule, navigation/filter/current-input binding)
- `retry_policy` (per operation class: retryable? max attempts, backoff, conditions, idempotency key required?)
- `auth_expiry` (401 handling: refresh token flow, max refresh attempts, protected cache clearing, failure behavior, redirect target, no refresh loop)
- `response_validation` (runtime schema/guard library, schema source, invalid shape behavior, malformed-response state)
- `pagination` (type: cursor/offset/keyset; stability disclosure; empty page behavior; end-of-list signal)
- `cache_strategy` (cache key, staleTime, gcTime, invalidation triggers, stale-while-revalidate behavior, permission/session reset)
- `optimistic_updates` (pre-mutation state capture, rollback on error, conflict resolution)
- `error_mapping` (HTTP/problem code -> frontend state -> user-facing message -> recovery action; no internal details exposed)
- `response_contract_alignment` (fields consumed, optional/null/default handling, problem-details/violations mapping, version-skew or generated-client limit)
- `race_and_freshness_controls` (request identity, latest-input guard, current cursor/filter binding, stale cache behavior, background revalidation state)
- `security_privacy_controls` (tokens not logged, PII redaction, browser-exposed credential rule, connect-src or destination allowlist when relevant)
- `telemetry` (trace propagation headers; what is logged; what is NOT logged: tokens, PII)
- `changed_frontend_api_to_validation_map` (each operation, lifecycle state, retry/idempotency rule, auth expiry branch, response schema, cache invalidation, pagination edge, optimistic update, error mapping, and telemetry rule mapped to validator/test or residual risk)
- `handoff_boundaries` (what belongs to API contract, DTO/schema, error taxonomy, idempotency/retry, state management, security/privacy, frontend testing, or product copy review)
- `tests` (race/stale response, timeout, cancellation, retry dedup, auth expiry, permission/denied state, shape validation failure, pagination stability, cache invalidation, optimistic rollback)
- `evidence_limits` (what was not inspected or not run: server contract, real browser, deployed auth, production cache behavior, third-party API, full E2E, or accessibility behavior)

# Evidence Contract

Close a frontend API integration output only when it names selected mode, current source evidence inspected, graph/memory/trajectory reuse judgment, every operation lifecycle, cancellation and timeout policy, retry/idempotency decision, auth expiry behavior, runtime response validation, cache and pagination freshness, error mapping, security/privacy controls, changed-frontend-api-to-validation map, handoff boundaries, residual risk, and evidence limits. A generic "fetch with loading/error handling" or "use React Query" statement is not sufficient evidence.

# Benchmark Coverage

Improved frontend API integration plans reject common weak patterns: fetches without cancellation, last-response-wins search, mutation retry without idempotency, refresh loops, unvalidated response destructuring, raw error display, auth token logging, offset pagination without instability disclosure, stale cache after logout, optimistic update without rollback, contract-drifting mocks, and stale repository-memory claims about API clients. Detailed lifecycle, retry, cache, pagination, and race matrices belong in references so the body stays efficient.

# Routing Coverage

Route here when frontend HTTP/request lifecycle, response handling, cache freshness, retry, cancellation, auth expiry, pagination, optimistic update, or API-backed UI state is primary. Hand off when the primary concern is server operation contract (`api-contract-design`), DTO/field serialization (`dto-schema-design`), error taxonomy (`error-code-design`), state ownership and cache invalidation strategy (`state-management-design`), form submission authority (`form-validation-design`), test implementation (`frontend-testing`), or security review (`security-privacy-gate`).

# Quality Gate

The integration plan is complete only when:

1. Every request has AbortController cancellation with a defined trigger.
2. Stale responses are discarded or ignored when route, filter, cursor, or current input changes.
3. Retry policy declared per operation class; mutations not retried without idempotency key and safe server semantics.
4. Response shape validated with runtime schema or explicit guard before any field access.
5. 401 auth expiry handled with refresh-once pattern, protected cache reset, and failure redirect.
6. Timeout defined per request class; mutation timeout is treated as unknown outcome and does not trigger unsafe retry.
7. All optimistic updates have captured pre-mutation state, rollback, conflict handling, and user-visible error notification.
8. All error codes map to frontend states and user-facing recovery messages with no internal details.
9. Pagination type declared; offset pagination has UX stability disclosure and deterministic sort/tiebreaker when possible.
10. Cache keys, staleTime/gcTime, stale-while-revalidate state, invalidation triggers, and auth/session reset are explicit.
11. No auth tokens, secrets, provider credentials, raw response bodies with PII, or internal error details are logged or exposed.
12. Selected mode, source evidence, and graph/memory/trajectory reuse judgment are explicit.
13. Every operation, lifecycle state, retry/idempotency rule, auth branch, response schema, cache invalidation, pagination edge, optimistic update, error mapping, and telemetry rule maps to validation evidence or named residual risk.
14. Handoff boundaries and evidence limits are explicit so integration evidence is not over-claimed as server contract, deployed auth behavior, real-browser E2E coverage, or production third-party behavior.

# Used By

- frontend-change-builder
- data-api-contract-changer

# Handoff

Hand off to `api-contract-design` for endpoint behavior and schema; `dto-schema-design` for response type contracts; `error-code-design` for stable error taxonomy; `idempotency-retry-design` for server-side mutation deduplication; `frontend-testing` for request lifecycle test coverage.

# Completion Criteria

The capability is complete when **every API operation has a defined lifecycle (request, cancellation, timeout, retry, expiry, validation, error mapping) with no silent failure paths, no race conditions, no unsafe retries, and no raw API internals exposed to users**.
