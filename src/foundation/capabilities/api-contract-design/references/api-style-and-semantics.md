# API Style and Semantics Reference

Load this reference for L3+ API contract decisions, public/partner/mobile contracts, ambiguous protocol choices, retry/idempotency/status-code disputes, long-running operations, or versioning/deprecation design.

## API Style Selection Matrix

| Style | Pick when | Avoid when | Pagination | Versioning idiom |
| --- | --- | --- | --- | --- |
| REST + JSON over HTTP | Public, partner, mobile, browser-facing; CRUD-shaped resources; cacheable reads | High-frequency RPC inside one trust zone; strict schema evolution | Cursor preferred, or page/limit | URL prefix `/v1/` or `Accept: application/vnd.x+json;v=1` |
| gRPC | Internal east-west, low-latency, polyglot services, streaming | Browser clients without proxy; debuggability matters more than throughput | Cursor in request message | Package versioning `pkg.v1`, never break wire format |
| GraphQL | Aggregated read-heavy clients, mobile bandwidth-sensitive, many small resources | Side-effecting batch operations; cache-by-URL needs; n+1 cost is uncontrolled | Relay connections (`first`/`after`) | Field-level deprecation `@deprecated`; no version bumps |
| AsyncAPI / events | Producer/consumer decoupling, fan-out, audit, eventual consistency | Synchronous user-blocking flows where consistency must be immediate | Offset/sequence per partition | Schema registry plus compatibility mode |
| Webhooks | Notify external systems of events you own | When you need a response from the receiver synchronously | N/A, event-per-call | Versioned event type plus schema |
| Long-running operations | Work exceeds request timeout budget | Sub-second operations | Operation resource plus polling or callback | `operations/{id}` resource per Google AIP-151 |

## Idempotency and Method Semantics

| Method | Safe | Idempotent | Body | Cacheable | Notes |
| --- | --- | --- | --- | --- | --- |
| GET | yes | yes | no | yes | Never carry side effects |
| HEAD | yes | yes | no | yes | Identical to GET headers |
| OPTIONS | yes | yes | no | conditionally | CORS preflight |
| PUT | no | yes | yes | no | Full replacement; must be idempotent by definition |
| DELETE | no | yes | conditionally | no | Repeating must return `204`/`404` deterministically |
| POST | no | no by default | yes | conditionally | Require `Idempotency-Key` header for create/retryable |
| PATCH | no | no by default | yes | no | Use JSON Patch RFC 6902 or JSON Merge Patch RFC 7396; pick one and declare it |

## Status Code Discipline

| Code | Meaning | Common misuse |
| --- | --- | --- |
| 200 | Success with body | Used for created resources that should return 201 |
| 201 | Created; include `Location` header and body | Returned without `Location` |
| 202 | Accepted, async; include polling URL | Used for sync success |
| 204 | Success, no body | Returned with a body, which is illegal per RFC 9110 |
| 400 | Client malformed | Used for business-rule failures that should return 422 |
| 401 | Not authenticated | Conflated with 403 |
| 403 | Authenticated, not authorized | Returned to hide existence; use 404 instead when policy requires ambiguity |
| 404 | Not found | Returned for forbidden without a documented existence-hiding policy |
| 409 | State conflict | Used for any validation failure |
| 410 | Gone, permanently removed | Forgotten when deprecating endpoints |
| 422 | Semantic validation failure | Used for transport-level parse errors that should return 400 |
| 428 | Precondition required, such as `If-Match` | Skipped when optimistic concurrency is needed |
| 429 | Rate limited; include `Retry-After` | Returned without `Retry-After` |
| 5xx | Server fault | Used for client errors |

## Versioning Approach

Use no version bump for additive optional fields or new optional endpoints. Use a new public major version and a documented deprecation timeline for semantic changes, removals, required fields, or behavior changes that deployed clients can observe. Use expand-contract rollout for internal APIs, and in GraphQL prefer new fields plus `@deprecated(reason)` over version bumps.
