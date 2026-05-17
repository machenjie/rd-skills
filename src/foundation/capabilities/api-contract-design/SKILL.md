---
name: api-contract-design
description: Designs API contracts with request, response, errors, authentication, pagination, idempotency, compatibility, and describable HTTP semantics.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "26"
changeforge_version: 0.1.0
---

# Mission

Design API contracts that clients can implement safely under retries, version skew, partial failure, and adversarial input — through explicit requests, responses, errors, authentication, pagination, idempotency, concurrency control, and compatibility rules.

# When To Use

Use this capability when a change adds, removes, renames, versions, splits, merges, or alters: endpoints, methods, resources, payloads, status codes, error models, auth requirements, pagination, filtering, sorting, field semantics, rate limits, idempotency keys, webhook deliveries, long-running operation patterns, or content negotiation.

# Do Not Use When

Do not use this capability to expose internal functions, ORM entities, database tables, or domain aggregates directly without a stable contract boundary. Do not use it as a substitute for `dto-schema-design` (field-level validation), `error-code-design` (error taxonomy), `version-compatibility` (rollout across clients), or `authentication-authorization` (policy implementation).

# Non-Negotiable Rules

- Define request shape, response shape, status codes, error model, and auth/authorization requirements explicitly — defaults are not a contract.
- Define pagination, filtering, sorting, and partial response rules for any collection endpoint; never return unbounded lists.
- Define idempotency for every create, retryable, or side-effecting operation; document key scope, retention window, and replay semantics.
- Define compatibility expectations and a versioning/deprecation path; breaking changes require a migration plan before merge.
- HTTP APIs must be describable through OpenAPI ≥ 3.0 (or AsyncAPI for event APIs, gRPC `.proto` for gRPC, GraphQL SDL for GraphQL). Contract-first, not code-first reverse-derivation.
- Use stable, language-agnostic identifiers (UUID/ULID/opaque cursor), never database row ids in public contracts unless the resource is the database row by design.
- Return resource representations, not actions on internals; commands map to resources or RPC-style verbs explicitly chosen.
- Time values are RFC 3339 UTC with explicit offset; monetary values use ISO 4217 currency + minor-unit integer (never floats).
- Rate-limit responses (`429`) and authentication failures (`401`/`403`) must distinguish "missing", "invalid", "expired", "insufficient scope", and "rate limited" — never collapse.
- Webhooks/callbacks require signed payloads, replay protection, retry policy, and timeout contract.

# Industry Benchmarks

Anchor against: **OpenAPI 3.1 / JSON Schema 2020-12**, **AsyncAPI 2.6+** for event APIs, **gRPC + Protobuf 3** for low-latency internal RPC, **GraphQL** spec (October 2021) + Relay cursor connection spec, **RFC 9110/9111/9112** (HTTP semantics, caching, syntax), **RFC 7807 / 9457 Problem Details for HTTP APIs** (error model), **RFC 5988 / 8288 Web Linking** (HATEOAS where applicable), **RFC 7234** caching, **RFC 6585** additional status codes (`429`), **RFC 7231 §4.2** safe/idempotent methods, **RFC 6749 / 6750 OAuth 2.0**, **RFC 7519 JWT** (when chosen), **OWASP API Security Top 10 (2023)**, **Google AIPs (aip.dev)**, **Microsoft REST API Guidelines**, **Zalando RESTful API Guidelines**, **PayPal API Style Guide**, **Stripe API design** (resource modeling, idempotency-key header, expandable fields, pagination), **Consumer-Driven Contracts (Pact)**, **JSON:API** spec where applicable. For SLO/error budgets follow Google SRE Workbook.

### API Style Selection Matrix

| Style | Pick when | Avoid when | Pagination | Versioning idiom |
| --- | --- | --- | --- | --- |
| **REST + JSON over HTTP** | Public, partner, mobile, browser-facing; CRUD-shaped resources; cacheable reads | High-frequency RPC inside one trust zone; strict schema evolution | Cursor (preferred) or page/limit | URL prefix `/v1/` or `Accept: application/vnd.x+json;v=1` |
| **gRPC** | Internal east-west, low-latency, polyglot services, streaming | Browser clients without proxy; debuggability matters more than throughput | Cursor in request message | Package versioning `pkg.v1`, never break wire format |
| **GraphQL** | Aggregated read-heavy clients, mobile bandwidth-sensitive, many small resources | Side-effecting batch operations; cache-by-URL needs; n+1 cost is uncontrolled | Relay connections (`first`/`after`) | Field-level deprecation `@deprecated`; no version bumps |
| **AsyncAPI / events** | Producer/consumer decoupling, fan-out, audit, eventual consistency | Synchronous user-blocking flows where consistency must be immediate | Offset/sequence per partition | Schema registry + compatibility mode (BACKWARD/FORWARD) |
| **Webhooks** | Notify external systems of events you own | When you need a response from the receiver synchronously | N/A (event-per-call) | Versioned event type + schema |
| **Long-running operations** | Work > a request timeout budget | Sub-second operations | Operation resource + polling or callback | `operations/{id}` resource per Google AIP-151 |

### Idempotency & Method Semantics

| Method | Safe | Idempotent | Body | Cacheable | Notes |
| --- | --- | --- | --- | --- | --- |
| GET | ✓ | ✓ | no | ✓ | Never carry side effects |
| HEAD | ✓ | ✓ | no | ✓ | Identical to GET headers |
| OPTIONS | ✓ | ✓ | no | conditionally | CORS preflight |
| PUT | ✗ | ✓ | yes | no | Full replacement; must be idempotent by definition |
| DELETE | ✗ | ✓ | conditionally | no | Repeating must return `204`/`404` deterministically |
| POST | ✗ | ✗ by default | yes | conditionally | Require `Idempotency-Key` header for create/retryable |
| PATCH | ✗ | ✗ by default | yes | no | Use JSON Patch RFC 6902 or JSON Merge Patch RFC 7396 — pick one and declare it |

### Status Code Discipline (must-knows, not exhaustive)

| Code | Meaning | Common misuse |
| --- | --- | --- |
| 200 | Success with body | Used for created resources (should be 201) |
| 201 | Created — include `Location` header and body | Returned without `Location` |
| 202 | Accepted, async — include polling URL | Used for sync success |
| 204 | Success, no body | Returned with a body (illegal per RFC 9110) |
| 400 | Client malformed | Used for business-rule failures (should be 422) |
| 401 | Not authenticated | Conflated with 403 |
| 403 | Authenticated, not authorized | Returned to hide existence (use 404 instead per policy) |
| 404 | Not found | Returned for forbidden, leaking ambiguity |
| 409 | State conflict | Used for any validation failure |
| 410 | Gone — permanently removed | Forgotten when deprecating endpoints |
| 422 | Semantic validation failure | Used for transport-level parse errors (should be 400) |
| 428 | Precondition required (e.g., `If-Match`) | Skipped when optimistic concurrency is needed |
| 429 | Rate limited — include `Retry-After` | Returned without `Retry-After` |
| 5xx | Server fault | Used for client errors |

# Selection Rules

Select this capability when **client-visible API behavior** is the primary decision. Adjacent routing:

- Prefer `dto-schema-design` when field-level serialization, validation rules, defaults, and nullability dominate.
- Prefer `error-code-design` when the error taxonomy and client remediation guidance are the main work.
- Prefer `version-compatibility` when rollout across old and new clients is the dominant risk.
- Prefer `event-driven-architecture` or `message-queue-design` for async producer/consumer topology.
- Prefer `authentication-authorization` for policy modeling and enforcement.
- Prefer `idempotency-retry-design` when duplicate side effects are the headline risk.
- Use **with** `frontend-api-integration` to ensure the contract is consumable, not just specifiable.

# Risk Escalation Rules

Escalate when the API is: public, partner-facing, mobile-client-facing (long client upgrade tail), high-volume (> 100 RPS sustained), payment / money-movement, permission-sensitive, PII-bearing, regulated (PCI/HIPAA/PSD2/GDPR), incompatible with deployed clients, or when a deprecation window shorter than 6 months is proposed for an external API. Escalate to architecture for cross-service contracts, to security for auth/scope changes, to product for breaking changes affecting paying customers, to SRE when the contract change shifts traffic patterns (e.g., chatty → batch).

# Critical Details

Contracts describe **behavior, not only shapes**. The following details cause production incidents when ignored:

- **Authentication and authorization are part of the contract.** Document required scopes, roles, tenant scoping, and the exact failure shape per failure class.
- **Errors need stable codes and client actions.** Use RFC 7807/9457 `application/problem+json` with `type`, `title`, `status`, `detail`, `instance`, and stable application-specific `code` and `retryable` boolean.
- **Pagination must be deterministic under concurrent writes.** Prefer opaque cursors over offset/limit; offsets skip or duplicate rows when the dataset mutates. Cursors must encode sort key + tiebreaker. Document max page size; reject larger.
- **Idempotency keys** need: client-supplied scope (per-operation), server-side retention window (≥ 24h typical, ≥ 7d for billing), response replay (same body + status for same key), key-collision rejection (`409` if same key with different payload), and storage cost ownership.
- **Optimistic concurrency.** Use `ETag` + `If-Match`/`If-None-Match` or a `version` field for mutable resources. Returning a `412 Precondition Failed` is the contract.
- **Partial responses & sparse fieldsets.** If supported, document the projection grammar (`fields=`, GraphQL selection) and the always-included minimal set.
- **Filtering grammar.** Avoid ad-hoc string DSLs. Either RHS-colon (`status:active`), structured query params (`filter[status]=active`), or a documented expression grammar (RSQL/CQL). Reject unknown filter fields explicitly, not silently.
- **Sorting.** Always define a deterministic tiebreaker (typically id) to make pagination stable.
- **Time, numbers, money.** RFC 3339 UTC, integers for ids, decimal strings or minor-unit integers for money. Never floats for monetary values. Document timezone semantics for dates that are not instants.
- **Internationalization.** `Accept-Language` honored or rejected explicitly; localized fields documented; locale-dependent formats (dates, numbers) returned in canonical form, not display form.
- **Rate limiting.** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers (or RFC 9180 draft `RateLimit-*`); `429` with `Retry-After` (seconds or HTTP-date).
- **Long-running operations.** Return `202` with an operation resource (Google AIP-151): `name`, `done`, `error`, `response`. Polling and webhook callback semantics documented.
- **Compatibility classes** (must declare): additive (safe), additive-optional (safe), additive-required (breaking), removal (breaking), semantic change (breaking even if shape unchanged), enum addition (often breaking for strict clients).
- **Hide persistence internals.** Do not expose ORM relation graphs, surrogate keys, or transaction-only fields. Hide implementation details (auto-increment ids, internal status enums) behind stable representations.
- **Content negotiation.** Pin `Content-Type` and `Accept`; reject `*/*` for write paths in machine APIs.
- **Webhook security.** HMAC-SHA256 signature over body + timestamp; replay protection via timestamp tolerance (≤ 5 min) and nonce; retry policy (exponential backoff, ≥ 24h horizon, DLQ).

### Decision Tree: Versioning Approach

```
Is the change additive-optional (new optional field, new endpoint)?
├─ Yes → No version bump; document under current version; semver minor in changelog.
└─ No → Is the change a semantic change to an existing field/code?
        ├─ Yes → BREAKING. Choose:
        │       ├─ Public/partner API → New major version (`/v2/`) + deprecation timeline ≥ 12 months.
        │       ├─ Internal API → Coordinated rollout via expand-contract (add new, dual-write/read, retire old).
        │       └─ GraphQL → New field + `@deprecated(reason)`; never bump.
        └─ No → Is the change a removal?
                ├─ Yes → Mark `Sunset` + `Deprecation` headers (RFC 8594, draft); retain ≥ 1 release; then 410.
                └─ No → Re-classify; you are not yet ready.
```

# Failure Modes

- Response shape changes break clients because fields were treated informally; no schema registry; no contract test.
- Collection endpoints lack pagination, return unbounded arrays, or use offset pagination over mutating data → duplicate/missing rows.
- Retried POST requests duplicate side effects because `Idempotency-Key` is undocumented or not enforced.
- Errors are raw stack traces or inconsistent strings; clients string-match on `message` and break on every change.
- API docs are reverse-derived from code annotations and drift from runtime behavior; no contract test verifies them.
- `200 OK` is returned with an `error` field in the body → defeats HTTP semantics, breaks caches, breaks observability.
- `403` vs `404` policy is undocumented, leaking resource existence.
- Floats used for money → silent rounding loss.
- Surrogate database ids exposed → cannot change storage, cannot shard, leaks row counts via enumeration.
- Enum values added without compatibility mode → strict clients (gRPC, code-generated) reject responses.
- Filtering uses ad-hoc string DSL parsed by `eval` or unbounded RegExp → injection / ReDoS.
- Webhook lacks signature or timestamp → forgery and replay.
- Long-running operation returns `200` with `status: "pending"` → clients confuse async with sync; cannot cancel.
- Deprecation is announced in a blog post, not in `Deprecation`/`Sunset` headers and the spec.
- "Wrapper" envelope (`{ data, meta, error }`) is added inconsistently — some endpoints, not others.

# Output Contract

Return an API contract specification containing, for each operation:

- `operation_id` (stable, unique)
- `method`, `path` (or RPC service.method)
- `summary`, `description`, `tags`
- `auth_requirements` (scheme, scopes, tenant scope)
- `request`: headers, path params, query params, body schema (ref to DTO), examples
- `response`: per status code → headers, body schema, examples
- `error_responses`: per error class → status, RFC 7807 problem document with stable `code`, `retryable`, `remediation`
- `idempotency`: required? key header name, scope, retention, replay semantics
- `pagination`: style (cursor/offset/none), max page size, sort keys, tiebreaker
- `concurrency`: ETag/version, precondition headers, conflict response
- `rate_limit`: limits, headers, retry guidance
- `caching`: `Cache-Control`, `ETag`, `Vary` rules
- `compatibility`: change class (additive / breaking), affected clients, deprecation/sunset dates
- `versioning`: version selector, current/previous/next
- `examples`: complete request/response pairs including at least one error
- `contract_tests`: Pact/OpenAPI-Examples/Schemathesis test ids that prove the contract
- `observability`: emitted metrics (latency, error rate by code), trace span name, log correlation fields
- `security_notes`: input validation rules, sensitive-field redaction in logs, scope-vs-data checks

Deliverable artifact: an OpenAPI 3.1 / AsyncAPI / `.proto` / GraphQL SDL document **plus** a human-readable change summary classifying each operation as new / additive / breaking / removed.

# Quality Gate

The contract passes only when:

1. A client developer can implement against the spec **without reading server source** and without asking clarifying questions on auth, pagination, errors, idempotency, or compatibility.
2. The spec is machine-validated (e.g., Spectral lint passes; OpenAPI validator passes; Schemathesis property tests pass on a running server).
3. Every operation has at least one success and one error example, and the examples validate against the schema.
4. Every breaking change has an explicit migration path, a deprecation window, and a named owner.
5. Contract tests (consumer-driven where there is a known consumer; provider tests otherwise) exist and run in CI.
6. Auth scopes match `authentication-authorization` outputs; error codes match `error-code-design`; DTOs match `dto-schema-design`.

# Used By

- data-api-contract-changer
- integration-change-builder

# Handoff

Hand off to `dto-schema-design` for field validation/serialization detail; `error-code-design` for the canonical error taxonomy; `version-compatibility` for rollout sequencing across clients; `security-privacy-gate` for sensitive-data exposure and OWASP API Top 10 review; `idempotency-retry-design` for retry safety detail; `frontend-api-integration` and `controller-api-implementation` for consumer/provider implementation; `observability` and `reliability-observability-gate` for SLI/SLO and rate-limit alerting.

# Completion Criteria

The capability is complete when the API is **stable, describable, testable, and safe for clients across retries, version skew, partial failure, and hostile input** — and when every change class (additive, breaking, removed) is named explicitly, with rollout, deprecation, and verification owned by a named party.
