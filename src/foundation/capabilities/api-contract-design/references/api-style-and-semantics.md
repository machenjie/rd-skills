# API Style and Semantics Reference

Load this reference for L3+ API contract decisions, public/partner/mobile contracts, ambiguous protocol choices, retry/idempotency/status-code disputes, long-running operations, or versioning/deprecation design.

## API Style Selection Matrix

| Style | Pick when | Avoid when | Pagination | Versioning idiom |
| --- | --- | --- | --- | --- |
| REST + JSON over HTTP | Public, partner, mobile, browser-facing; CRUD-shaped resources; cacheable reads | High-frequency RPC inside one trust zone; strict schema evolution | Cursor preferred, or page/limit | URL prefix `/v1/` or `Accept: application/vnd.x+json;v=1` |
| gRPC | Internal east-west, low-latency, polyglot services, streaming | Browser clients without proxy; debuggability matters more than throughput | Cursor in request message | Version protobuf packages (for example, `pkg.v1`); preserve wire compatibility within a deployed version, and introduce a new version with consumer migration and deprecation for an incompatible change. |
| GraphQL | Aggregated read-heavy clients, mobile bandwidth-sensitive, many small resources | Side-effecting batch operations; cache-by-URL needs; n+1 cost is uncontrolled | Relay connections (`first`/`after`) | Field-level addition or deprecation under the governing schema and consumer-compatibility policy |
| AsyncAPI / events | Producer/consumer decoupling, fan-out, audit, eventual consistency | Synchronous user-blocking flows where consistency must be immediate | Offset/sequence per partition | Schema registry plus compatibility mode |
| Webhooks | Notify external systems of events you own | When you need a response from the receiver synchronously | N/A, event-per-call | Versioned event type plus schema |
| Long-running operations | Work exceeds request timeout budget | Sub-second operations | Operation resource plus polling or callback | `operations/{id}` resource per Google AIP-151 |

## Idempotency and Method Semantics

| Method | Safe | Idempotent | Body | Cacheable | Notes |
| --- | --- | --- | --- | --- | --- |
| GET | yes | yes | no | yes | For an operation exposed with GET, requested semantics remain non-mutating; incidental server effects such as logging or accounting neither change the requested resource state nor create a client-visible mutation contract. |
| HEAD | yes | yes | no | yes | Identical to GET headers |
| OPTIONS | yes | yes | no | conditionally | CORS preflight |
| PUT | no | yes | yes | no | When the contract defines full replacement, identical requests preserve the same intended resource-state effect; incidental logging or accounting remains outside that effect. |
| DELETE | no | yes | conditionally | no | Define repeat-DELETE response semantics and preserve an idempotent resource outcome; select `200`, `202`, `204`, `404`, `410`, or another documented status from the current contract and async/deletion model. |
| POST | no | no by default | yes | conditionally | When duplicate effects are possible, define a contract-owned replay key or operation identity; declare its carrier, scope, expiry, mismatch handling, and result replay. |
| PATCH | no | no by default | yes | no | Select semantics from the operation: JSON Patch for ordered edit operations, JSON Merge Patch for document-merge semantics, or a domain command for invariant-bearing transitions; declare concurrency and replay behavior. |

## Status Code Discipline

| Code | Meaning | Common misuse |
| --- | --- | --- |
| 200 | Successful result; response content follows the method and representation contract | Used for created resources whose contract selects 201 |
| 201 | Created; identify the primary resource and select `Location` and response content from the method, representation, and governing contract | Requires or omits `Location` or content without applying that contract |
| 202 | Accepted, async; include polling URL | Used for sync success |
| 204 | Success, no body | Returned with a body, which is illegal per RFC 9110 |
| 400 | Malformed or invalid request when selected by the governing protocol and error contract | Defaults business-rule or representation failures to 422 without applying that contract |
| 401 | Not authenticated | Conflated with 403 |
| 403 | Authenticated, not authorized | Returned to hide existence; use 404 instead when policy requires ambiguity |
| 404 | Not found | Returned for forbidden without a documented existence-hiding policy |
| 409 | State conflict | Used for any validation failure |
| 410 | Gone, permanently removed | Forgotten when deprecating endpoints |
| 422 | Content is understood but its instructions cannot be processed, when the method, representation, and governing contract select this status | Used without checking those method and contract semantics |
| 428 | Precondition required, such as `If-Match` | Skipped when optimistic concurrency is needed |
| 429 | Rate limited; include `Retry-After` only when the governing contract provides an authoritative retry time | Invents or omits `Retry-After` contrary to that contract |
| 5xx | Server fault | Used for client errors |

## Versioning Approach

Apply the governing published API and consumer-compatibility policy before selecting a versioning mechanism.
An additive field or endpoint avoids a version bump only when consumer evidence preserves validation, exhaustive matching, generated clients, defaults, ordering, and side effects. Otherwise use the policy-selected migration.
For removals, required fields, or observable semantic changes, choose a major version, compatibility bridge, or coordinated migration from governing policy and consumer evidence. Do not infer the mechanism from the change label.
Document the applicable migration and deprecation timeline, including mixed-version behavior and rollback.
Use expand-contract rollout for internal APIs when current writer/reader coordination and rollback evidence support it. In GraphQL, prefer new fields plus `@deprecated(reason)` when schema policy and consumer proof preserve semantics; otherwise use the policy-selected coordinated migration.
