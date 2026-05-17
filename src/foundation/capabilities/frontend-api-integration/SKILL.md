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

# Non-Negotiable Rules

- **Every request must have a defined cancellation point.** When a user navigates away from a view while a request is in flight, the request must be cancelled using `AbortController`. Without cancellation: stale responses can overwrite newer state; memory leaks occur in SPA frameworks when state is updated after component unmount; multiple in-flight requests for the same resource create race conditions.
- **Retries are only safe for idempotent operations.** GET and HEAD requests may be retried unconditionally. POST, PUT, PATCH, DELETE mutations must not be retried unless: (1) the server returns a `Retry-After` header (transient 429/503), AND (2) the request includes an `Idempotency-Key` header that prevents duplicate effects on the server. Never retry a mutation silently on timeout — the operation state is unknown; the server may have committed it.
- **Response shape must be validated at the client boundary.** The frontend must not destructure or render API responses without validating the shape. Use a schema validation library (Zod, Valibot, Yup). Invalid/unexpected shapes must produce a specific "unexpected response" error state, not a JavaScript TypeError crash in the render tree.
- **Authentication expiry must never produce a broken page.** When a 401 Unauthorized response is received: attempt token refresh exactly once; if refresh succeeds, replay the original request; if refresh fails, redirect to login with the current URL as `next` parameter for post-login redirect; never display a raw 401 error to the user.
- **Optimistic updates must have a rollback path.** Any optimistic state mutation must store the previous state before applying the optimistic update. On server error, revert to the previous state and show an error notification. Without rollback, failed optimistic updates leave the UI in a permanently incorrect state.
- **Error messages must be user-actionable.** Map API error responses to user-facing messages before display. Never expose: HTTP status codes as user messages; internal error codes, stack traces, or exception class names; SQL or schema details. User message must identify what went wrong and what the user can do next (retry, contact support, check inputs).
- **Pagination must handle instability.** Cursor-based pagination is preferred over offset for any list that can be mutated. Offset pagination on mutable data: newly inserted records shift pages (records duplicated across pages); deleted records collapse pages (records skipped). When offset pagination is required for legacy reasons, document the instability and add a "new items may not appear immediately" UX disclosure.

# Industry Benchmarks

Anchor against: **Fetch API + AbortController** (WHATWG) — `AbortController.abort()` cancels in-flight `fetch()`; `AbortSignal.timeout(ms)` for request timeout (Node.js 17.3+, all modern browsers); `signal` parameter on `fetch()`. **React Query / TanStack Query** — `queryKey` deduplication; `staleTime` / `gcTime` cache config; `invalidateQueries()` for post-mutation invalidation; `useMutation` with `onMutate` (optimistic update) and `onError` (rollback); automatic retry with `retry` and `retryDelay` config. **SWR (Vercel)** — stale-while-revalidate RFC 5861; `revalidateOnFocus`, `revalidateOnReconnect`; `mutate()` for cache update. **Axios** — `CancelToken` (deprecated); `AbortController` since Axios 0.22; `interceptors.response` for global 401 handling; `timeout` config. **Zod** (TypeScript) — `z.object({}).parse(data)` throws `ZodError` with structured error details; `safeParse()` for non-throwing variant; use to validate API response shape before use. **RFC 7807 / RFC 9457** — Problem Details; parse `type`, `title`, `status`, `detail`, `instance`; map `violations[]` to field errors. **RFC 5861** — stale-while-revalidate; allows serving stale cached content while revalidating in background. **IETF draft-ietf-httpapi-idempotency-key-header** — `Idempotency-Key: <UUID v4>` header for mutation retry safety. **Exponential backoff with jitter** (AWS Architecture Blog, 2015: "Exponential Backoff And Jitter") — `delay = min(cap, base * 2^attempt) + random_between(0, jitter_factor * delay)`; prevents thundering herd on retry. **Cursor pagination** (Relay Cursor Connections Specification; GraphQL Foundation) — stable page results regardless of insertions/deletions; `pageInfo.hasNextPage`, `endCursor`, `startCursor`. **OpenTelemetry** (CNCF) — propagate `traceparent` / `baggage` headers from frontend fetch to backend; enables end-to-end trace across browser and server. **Content Security Policy** (CSP, RFC 9239) — `connect-src` directive restricts fetch destinations; API base URLs must be allowlisted. **OWASP Secure Headers Project** — frontend API clients must not log auth tokens or response bodies containing PII to browser console in production builds.

### Request Lifecycle State Machine

```
States: idle | loading | success | error | cancelled | stale

idle:      No request pending; data not yet fetched
loading:   Request in flight; AbortController registered; timeout timer running
success:   Response received; shape validated; data committed to state/cache
error:     Response error (4xx/5xx) OR network error OR validation failure
  → 401:   Attempt token refresh → if success: replay request → if fail: redirect to /login?next=...
  → 429/503 with Retry-After: bounded retry with delay from header (max 3 attempts)
  → 5xx:   Bounded exponential retry for read operations only (max 3 attempts)
  → 4xx (non-401): No retry; map to user-facing error message; show recovery action
cancelled: AbortController.abort() called (navigation, user cancel, superseded request)
  → No state update after cancel; discard response if received after abort
stale:     Cached data displayed; background revalidation in flight (stale-while-revalidate)

Timeout:
  Per request class:
    Page data (SSR/CSR):      5,000ms default
    User-initiated mutation:  10,000ms default
    Background revalidation:  30,000ms default
  On timeout: treat as unknown outcome; do NOT retry a mutation on timeout without idempotency key
```

### Retry Policy by Operation Class

| Operation | HTTP method | Retry on network error | Retry on 429/503 | Retry on 5xx | Retry on timeout | Condition |
| --- | --- | --- | --- | --- | --- | --- |
| Read (list, detail) | GET | ✅ max 3 | ✅ max 3 + Retry-After | ✅ max 3 | ✅ max 3 | No condition needed |
| Mutation (create) | POST | ❌ | ✅ if Idempotency-Key | ✅ if Idempotency-Key | ❌ unknown outcome | Idempotency-Key required |
| Mutation (update) | PUT/PATCH | ❌ | ✅ if Idempotency-Key | ✅ if Idempotency-Key | ❌ unknown outcome | Idempotency-Key required |
| Mutation (delete) | DELETE | ❌ | ✅ max 1 | ✅ max 1 | ❌ | May already be deleted |
| File upload | POST/PUT | ❌ (multipart) | ✅ if resumable | ❌ | ❌ | Use resumable upload protocol |
| Auth token refresh | POST | ✅ max 1 | ❌ | ❌ | ✅ max 1 | Exactly once; fail → logout |

### Response Validation Pattern

```typescript
// Define shape with Zod at module boundary
import { z } from "zod";

const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  role: z.enum(["admin", "member", "viewer"]),
  createdAt: z.string().datetime(),
});

type User = z.infer<typeof UserSchema>;

async function fetchUser(id: string, signal: AbortSignal): Promise<User> {
  const response = await fetch(`/api/users/${id}`, { signal });
  if (!response.ok) {
    throw new ApiError(response.status, await response.json());
  }
  const raw = await response.json();
  // Validate shape — throws ZodError on unexpected response
  return UserSchema.parse(raw);
}
// ZodError is caught by error boundary → renders "unexpected response" state
// NOT: const data = await response.json(); return data.user.role; // crashes on missing field
```

### Pagination Selection

| Criterion | Cursor-based | Offset-based | Keyset (seek method) |
| --- | --- | --- | --- |
| Data stability | ✅ Stable across inserts/deletes | ❌ Unstable; records skip/dup | ✅ Stable |
| Random page access | ❌ No | ✅ Yes | ❌ No |
| Performance at depth | ✅ O(1) cursor lookup | ❌ O(N) for large OFFSET | ✅ O(log N) with index |
| Suitable for | Infinite scroll, feeds, timelines | Static reports, page numbers | Large tables, audit logs |
| UX disclosure needed | No | ✅ "New items may not appear" | No |

# Selection Rules

Select this capability when **frontend data fetching and request lifecycle** are the primary design concern. Adjacent routing:

- Prefer `form-validation-design` when the primary concern is form field validation, submission state machine, and duplicate-submit protection.
- Prefer `api-contract-design` when the primary concern is the server-side API contract (endpoint definitions, request/response schemas).
- Prefer `state-management-design` when the primary concern is client-side state ownership, derived state, and cross-component cache invalidation.
- Prefer `idempotency-retry-design` when the primary concern is server-side deduplication implementation for retried mutations.

# Risk Escalation Rules

Escalate when: a mutation request handles payment, order creation, account deletion, or bulk data modification; authentication token storage or refresh logic is being introduced or changed (XSS attack surface); a third-party API call exposes credentials to the browser; an API response contains PII and is being logged or cached without redaction; optimistic updates are applied to financial or inventory data.

# Critical Details

Frontend API integration fails silently when assumptions about network conditions are not codified. Precision failures:

- **Race condition: last-write-wins on concurrent fetches.** User types in a search box; request A fires for "ali", request B fires for "alice". Response B arrives first (faster query), response A arrives second. UI renders results for "ali" instead of "alice". Fix: cancel request A when request B fires using AbortController; accept only the response matching the current input value.
- **Token refresh loop.** A 401 triggers a token refresh. The refresh also fails with 401. The code retries the refresh. Infinite loop. Token refresh must be attempted exactly once. On refresh failure: stop, clear session, redirect to login. Never retry a failed refresh.
- **Optimistic update not rolled back.** User marks a task complete (optimistic UI: task immediately disappears from list). Server returns 500. The task is gone from the UI but not from the database. User thinks the task is complete. Fix: store pre-mutation state; on error, revert and show error toast.
- **Undefined field access on unexpected response.** API temporarily returns `{"items": null}` instead of `{"items": []}`. Frontend renders `items.map(...)` → `TypeError: Cannot read properties of null`. Zod validation at the boundary converts this to an explicit "unexpected response" error state before the render tree sees the data.
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

# Output Contract

Return a frontend API integration plan with:

- `operations` (name, HTTP method, endpoint, purpose, mutating/read, optimistic update?)
- `request_lifecycle` (per operation: AbortController usage, timeout, cancellation trigger)
- `retry_policy` (per operation class: retryable? max attempts, backoff, conditions, idempotency key required?)
- `auth_expiry` (401 handling: refresh token flow, max refresh attempts, failure behavior, redirect target)
- `response_validation` (schema library, schema definition, invalid shape behavior)
- `pagination` (type: cursor/offset/keyset; stability disclosure; empty page behavior; end-of-list signal)
- `cache_strategy` (staleTime, gcTime, invalidation triggers, stale-while-revalidate behavior)
- `optimistic_updates` (pre-mutation state capture, rollback on error, conflict resolution)
- `error_mapping` (status code → user-facing message → recovery action; no internal details exposed)
- `telemetry` (trace propagation headers; what is logged; what is NOT logged: tokens, PII)
- `tests` (race condition test, retry dedup test, auth expiry flow test, shape validation failure test, optimistic rollback test)

# Quality Gate

The integration plan is complete only when:

1. Every request has AbortController cancellation with a defined trigger.
2. Retry policy declared per operation class; mutations not retried without idempotency key.
3. Response shape validated with schema library before any field access.
4. 401 auth expiry handled: refresh-once pattern with failure redirect.
5. Timeout defined per request class; mutation timeout does not trigger retry.
6. All optimistic updates have a captured pre-mutation state and rollback on error.
7. All error codes mapped to user-facing messages with no internal details.
8. Pagination type declared; offset pagination has UX stability disclosure.
9. No auth tokens or PII logged in error handlers or telemetry.
10. Tests cover: race condition, retry dedup, auth expiry, shape validation failure, optimistic rollback.

# Used By

- frontend-change-builder
- data-api-contract-changer

# Handoff

Hand off to `api-contract-design` for endpoint behavior and schema; `dto-schema-design` for response type contracts; `error-code-design` for stable error taxonomy; `idempotency-retry-design` for server-side mutation deduplication; `frontend-testing` for request lifecycle test coverage.

# Completion Criteria

The capability is complete when **every API operation has a defined lifecycle (request, cancellation, timeout, retry, expiry, validation, error mapping) with no silent failure paths, no race conditions, no unsafe retries, and no raw API internals exposed to users**.
