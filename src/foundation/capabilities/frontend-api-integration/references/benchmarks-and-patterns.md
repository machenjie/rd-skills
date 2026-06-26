# Frontend API Integration Benchmarks And Patterns

Use this reference when `frontend-api-integration` output needs more detail than the `SKILL.md` body should carry efficiently. Keep the main skill body focused on routing, lifecycle decisions, output evidence, and gates; use this file for benchmark anchors, request state machines, retry matrices, response/error mapping, race and cache controls, graph/memory/trajectory coupling, and anti-pattern review.

## Benchmark Anchors

- Fetch API and AbortController: pass `signal` to `fetch`, cancel superseded requests, and use timeout signals or equivalent timers.
- TanStack Query / React Query: query keys, staleTime, gcTime, invalidation, optimistic updates, and retry configuration.
- SWR: stale-while-revalidate, revalidate on focus/reconnect, and mutate-based cache updates.
- Axios: AbortController support in modern versions and response interceptors for global 401 handling.
- Runtime response validation: Zod, Valibot, Yup, generated schema guards, or equivalent boundary validation.
- RFC 7807 and RFC 9457 Problem Details: `type`, `title`, `status`, `detail`, `instance`, stable `code`, and field-level `violations`.
- RFC 5861 stale-while-revalidate and stale-if-error patterns for cache freshness behavior.
- Idempotency-Key practice: stable key per logical mutation when retry can duplicate effects.
- Exponential backoff with jitter: bounded attempts, max elapsed time, and thundering-herd avoidance.
- Relay Cursor Connections and keyset pagination: stable paging under inserts/deletes.
- OpenTelemetry TraceContext: propagate safe trace context without logging credentials or PII.
- CSP `connect-src`: restrict browser API destinations when the frontend can call external hosts.
- OWASP API Security Top 10 and ASVS: auth, object authorization, token exposure, and safe error disclosure.
- MSW or equivalent network-level mocks: align frontend fixtures with API contracts instead of mocking internals.

## Request Lifecycle State Machine

```text
idle
  No request pending; no data loaded for this operation.

loading
  Request in flight; request identity recorded; cancellation/timeout registered.

success
  Response received; status mapped; shape validated; data committed to state/cache.

error
  Response error, network error, timeout, or validation failure.
  401: refresh once, replay original request if refresh succeeds, otherwise redirect.
  403/404: map according to existence-leakage policy and permission UI.
  409/412: conflict or stale version; ask user to refresh or resolve.
  422/400 with violations: map to field/form/global state where relevant.
  429/503 with Retry-After: bounded retry for safe operations.
  5xx: bounded retry for reads only unless mutation idempotency is proven.

cancelled
  User navigated away, filters changed, a newer request superseded it, or user cancelled.
  No state update after cancel; delayed responses must be ignored.

stale
  Cached data displayed while background revalidation runs; UI communicates refresh state.

timeout
  Request exceeded the operation budget.
  Mutation timeout is unknown outcome, not proof of cancellation.
```

## Retry Policy By Operation Class

| Operation | Method | Network error | 429/503 | 5xx | Timeout | Required condition |
| --- | --- | --- | --- | --- | --- | --- |
| Read list/detail | GET/HEAD | Retry bounded | Retry with Retry-After or jitter | Retry bounded | Retry bounded | Safe method |
| Create mutation | POST | Do not auto-retry | Retry only with idempotency key | Retry only with idempotency key | Do not auto-retry | Server dedupe and replay semantics |
| Update mutation | PUT/PATCH | Do not auto-retry | Retry only with idempotency key | Retry only with idempotency key | Do not auto-retry | Conflict and idempotency semantics |
| Delete mutation | DELETE | Do not auto-retry by default | Retry at most once when safe | Retry at most once when safe | Do not auto-retry | Delete may already have committed |
| File upload | POST/PUT | Do not retry multipart blindly | Retry only if resumable | Usually no retry | Do not auto-retry | Resumable upload contract |
| Auth refresh | POST | Retry at most once | Do not retry by default | Do not retry by default | Retry at most once | Refresh loop forbidden |

## Response And Error Mapping Matrix

| Signal | Frontend state | User recovery | Must not expose | Test obligation |
| --- | --- | --- | --- | --- |
| 200/201 | Success after validation. | Continue flow. | Raw unvalidated JSON. | Shape-valid success fixture. |
| 202 | Pending/processing, not durable success. | Poll, subscribe, or return later. | "Done" before final status. | Accepted-to-complete mapping test. |
| 204 | Success with no body. | Return to stable state. | Body field access. | No-body response test. |
| 400/422 with `violations` | Field/form/global validation state. | Fix specific input. | Raw schema/regex/internal field names. | Violation mapping test. |
| 401 | Refresh-once or sign-in redirect. | Sign in again. | Raw 401 page or refresh loop. | Refresh success/failure tests. |
| 403 | Permission-denied state. | Request access or leave. | Sensitive resource existence. | Denied-state test. |
| 404 | Not found or non-leaking denied state. | Go back, refresh, or request access. | Existence leak. | Not-found/denied mapping test. |
| 409/412 | Conflict or stale version state. | Refresh, merge, or retry after review. | Generic server error. | Conflict recovery test. |
| 429 | Rate-limited state. | Wait and retry when allowed. | Immediate retry storm. | Retry-After handling test. |
| 5xx | Server error state. | Retry read or contact support. | Stack trace/provider body. | Safe error message test. |
| Network error | Offline/dependency error state. | Retry or check connection. | Misleading validation error. | Network failure test. |
| Malformed response | Unexpected-response state. | Retry or report trace id. | Render crash. | Invalid-shape test. |

## Race And Freshness Controls

| Risk | Control | Evidence |
| --- | --- | --- |
| Search/filter stale response | Request identity includes current input/filter; cancel or ignore older request. | Two delayed response test proves latest input wins. |
| Navigation after request | Abort on route unmount or ignore state updates after unmount. | Navigation/unmount test. |
| Cursor mismatch | Response cursor must match current cursor/filter key before append. | Cursor-change test. |
| Cache pollution across user/session | Query keys include user/tenant scope where applicable; clear protected cache on sign-out/401. | Logout/cache reset test. |
| Optimistic rollback | Store previous cache/state before mutation and restore on error. | Rollback test with server failure. |
| Background revalidation | Keep stale data visible with explicit refresh indicator; do not replace with spinner-only blank state. | Stale-while-revalidate state test. |
| Offset instability | Prefer cursor/keyset; if offset remains, disclose instability and define refresh behavior. | Pagination edge test or residual risk. |

## Cache And Invalidation Matrix

| Cache item | Key contents | Freshness rule | Invalidation trigger | Reset trigger |
| --- | --- | --- | --- | --- |
| Detail view | Resource id, user/tenant scope, projection. | staleTime per product tolerance. | Update/delete mutation, permission change. | Sign-out, 401 failure, tenant switch. |
| List/feed | Filters, cursor base, sort, user/tenant scope. | Stale-while-revalidate for refreshable lists. | Create/update/delete affecting list membership. | Sign-out, 401 failure, tenant switch. |
| Permission-sensitive data | Actor, role/scope, resource id. | Short freshness or server revalidation. | 403/401, role change, admin update. | Sign-out, token refresh failure. |
| Optimistic mutation | Stable logical operation id. | Pending until durable response. | Success replaces optimistic state; failure rolls back. | Conflict, timeout unknown outcome, sign-out. |

## Pagination Selection

| Criterion | Cursor-based | Offset-based | Keyset/seek |
| --- | --- | --- | --- |
| Stable under inserts/deletes | Strong when cursor includes sort+tiebreaker. | Weak; can skip or duplicate. | Strong with indexed seek key. |
| Random page access | Usually no. | Yes. | Usually no. |
| Deep-page performance | Good. | Degrades with large offset. | Good with proper index. |
| Best fit | Feeds, timelines, infinite scroll. | Static reports and page-number UX. | Large tables and audit logs. |
| Disclosure needed | Usually no. | Yes when data can mutate. | Usually no. |

## Response Validation Pattern

```typescript
import { z } from "zod";

const ActivitySchema = z.object({
  id: z.string().uuid(),
  eventType: z.string().min(1),
  actorLabel: z.string().min(1),
  occurredAt: z.string().datetime(),
});

const ActivityPageSchema = z.object({
  items: z.array(ActivitySchema),
  nextCursor: z.string().nullable(),
});

async function fetchActivity(signal: AbortSignal): Promise<z.infer<typeof ActivityPageSchema>> {
  const response = await fetch("/api/activity", { signal });
  if (!response.ok) {
    throw await mapApiError(response);
  }
  const raw = await response.json();
  return ActivityPageSchema.parse(raw);
}
```

Boundary rule: the render tree receives parsed data or a typed "unexpected response" state. It never receives unvalidated JSON.

## Graph, Memory, And Trajectory Coupling

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current API client, route/component, cache wrapper, schema, mocks, and tests were inspected. | Graph proximity is treated as proof that lifecycle or tests exist. |
| Project memory | Prior API pattern has owner, timestamp, unchanged source path, matching library version, and current source confirmation. | Memory predates auth, cache, schema, pagination, or testing convention changes. |
| Execution trajectory | Validation ran after final integration edit and covered changed API states. | Evidence is stale, partial, or from a different component/client. |
| Generated client/schema | Current generated source and source contract align. | Generated client was hand-edited or not regenerated after contract changes. |
| Frontend tests | Mocks align with schema and state matrix. | Tests mock private client internals, stale fixtures, or happy path only. |

## Review Questions

1. Which operations exist and which are reads, mutations, uploads, or auth flows?
2. Which operation can be cancelled, which can only be ignored, and why?
3. Which response can arrive stale, and how is request identity checked?
4. Which mutations can duplicate side effects, and where is idempotency proven?
5. Which timeout outcomes are unknown, and what user copy avoids false cancellation?
6. Which runtime schema validates the response before rendering?
7. Which errors map to field, form, permission, not-found, conflict, rate-limit, unexpected-response, or global error states?
8. Which cache keys, invalidation triggers, and reset triggers exist?
9. Which tokens, PII, or provider payloads could leak through logs or telemetry?
10. Which source, graph, memory, trajectory, browser, server contract, or third-party evidence remains unverified?

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| No AbortController or stale ignore rule. | Old response overwrites current UI. | Cancel/ignore with request identity and test. |
| Retry POST on network error by default. | Duplicate side effects. | Require idempotency key or no retry. |
| Refresh token retry loop. | App hangs or hammers auth endpoint. | Refresh exactly once, then clear session/redirect. |
| TypeScript type used as runtime validation. | External JSON can still be malformed. | Runtime schema or explicit guard at boundary. |
| Raw backend/provider error shown. | Leaks internals and blocks user recovery. | Map to safe state and diagnostic trace id. |
| Authorization header logged with request config. | Token exposure. | Redact headers and sensitive payloads. |
| Offset pagination for active feed with no disclosure. | Duplicate/skipped records. | Cursor/keyset or instability disclosure. |
| Cache not cleared on sign-out. | Next user sees prior user's data. | Clear protected cache on logout/401 failure. |
| MSW fixture hand-crafted outside contract. | Tests pass with impossible shape. | Contract-aligned factory/schema fixture. |
| Project memory copied without current source check. | Stale pattern becomes new defect. | Inspect current source/tests/schema before reuse. |

## Handoff Boundaries

- Use `api-contract-design` when endpoint shape, status codes, auth requirements, or pagination contract is missing.
- Use `dto-schema-design` when field-level nullability, defaults, or serialization rules are missing.
- Use `error-code-design` when stable error taxonomy, retryability, trace id, or problem-details shape is missing.
- Use `idempotency-retry-design` when mutation retry or duplicate effect prevention is unresolved.
- Use `state-management-design` when source-of-truth, cache ownership, invalidation, or persisted state is primary.
- Use `frontend-testing` when the implementation needs component, API-backed, permission, state, or accessibility tests.
- Use `security-privacy-gate` when auth, token storage, exposed browser credentials, PII, or safe logging is in scope.
