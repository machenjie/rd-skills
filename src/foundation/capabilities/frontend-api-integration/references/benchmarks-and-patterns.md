# Frontend API Integration Benchmarks And Patterns

Load this reference when request lifecycle, cancellation, response/error mapping, retry, cache/race behavior, or runtime contract handling changes. Do not load it for server contract design or a synchronous local computation.

## Operation Contract

| Operation | Retry/cancellation decision | Required proof |
| --- | --- | --- |
| Read/list/detail | Bounded retry may be safe for transient failures; cancel or ignore superseded work. | Attempt/deadline policy, request identity, timeout, stale-result behavior, and load/error/empty states. |
| Create/update/delete | Do not auto-retry an unknown outcome unless server idempotency and result replay cover the exact logical operation. | Stable key/scope, conflict semantics, durable status/reconciliation, and duplicate fixture. |
| Upload/long operation | Resume only through the server/provider’s owned chunk/session/status contract. | Checkpoint identity, expiry, cancellation, partial cleanup, and final-state polling/subscription. |
| Auth refresh | Coordinate concurrent callers and attempt only within the current session policy. | One refresh owner, loop prevention, replay safety, failure reset, and protected-cache clearing. |

Represent applicable idle, loading, stale/revalidating, success, accepted/pending, error, cancelled/ignored, timeout, conflict, partial, and unknown-outcome states. Cancellation stops local interest; it does not prove a remote mutation was cancelled.

## Boundary Mapping

- Decode status and error codes through the current contract: validation violations, unauthenticated, denied/non-leaking not-found, conflict/stale version, rate limit, dependency/server failure, network/offline, and malformed response need different recovery only when those distinctions exist.
- Validate untrusted wire data before render/cache commitment through generated contracts, a runtime schema, or an equivalent checked decoder, not static types alone.
- At a client-visible untrusted boundary, map server or provider failures to stable safe error fields and an available correlation identifier. Redact stack traces, raw provider or constraint detail, credentials, authorization headers, tokens, and sensitive request bodies.
- Logs and telemetry exclude tokens, PII, and raw provider payloads. Propagate an approved trace context across each actual client/gateway/service boundary or generate one at the owning boundary. Verify runtime emission, correlation, redaction, and label/cardinality safety.
- For delayed search/filter/navigation responses, bind identity to the current params/query/cursor and cancel or ignore older results. Appending a page requires the same filter/sort/cursor base that issued it.

## Cache, Freshness, And Pagination

Cache keys include every response-changing resource, actor/tenant, filter, sort, cursor, projection, and locale dimension. Define freshness, stale display, invalidation after each mutation/event, and reset on logout, 401 failure, user/tenant switch, or permission change. Optimistic updates snapshot all affected views and roll back, reconcile, or expose partial/unknown outcome.

Choose cursor/keyset, offset, or bounded static pagination from mutation rate, stable ordering/tie-breaker, deep-page access, query/index support, and user expectations. Offset instability is acceptable only with an explicit refresh/duplicate/skip contract.

## Evidence And Proof Limits

Inspect current clients, generated schema/types, cache/query wrappers, auth interceptors, components/routes, network mocks, and tests. Contract-aligned fixtures prove only represented responses; local timing tests do not prove production latency, provider retry behavior, browser cancellation, deployed auth coordination, or unknown consumers.

Reject blind mutation retries, refresh loops, unvalidated JSON entering render state, and raw server/provider errors. Also reject caches surviving identity changes, hand-written impossible fixtures, offset paging without an instability decision, and stale responses that can overwrite current UI.

Route missing endpoint/status/pagination contracts to `api-contract-design`, fields to `dto-schema-design`, errors to `error-code-design`, duplicate effects to `idempotency-retry-design`, cache ownership to `state-management-design`, sensitive browser data to `security-privacy-gate`, and executable network/state proof to `frontend-testing`.
