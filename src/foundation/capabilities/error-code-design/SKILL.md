---
name: error-code-design
description: Designs stable, actionable, product-grade error responses and prevents raw internal exceptions from becoming client contracts.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "28"
changeforge_version: 0.1.0
---

# Mission

Design **stable, safe, actionable, and diagnosable error responses** — structured so that clients can branch on machine-readable codes (not fragile strings), users receive safe explanations of what to do next, operators can trace failures via correlation IDs, and no internal implementation details (stack traces, SQL errors, internal class names, provider messages) are ever exposed in product-facing responses.

# When To Use

Use this capability when a change: defines new API error response shapes; maps domain exceptions to HTTP status codes; designs gRPC error status codes and detail types; creates error code taxonomies for a new service or subdomain; adds field-level validation error responses; designs retry-safe error semantics; adds correlation IDs or trace propagation to error responses; localizes user-facing error messages; defines error logging and diagnostic separation; or establishes error catalog governance for a product.

# Do Not Use When

Do not use this capability to expose raw exceptions as error bodies — that is prohibited, not a design option. Do not use it when the primary concern is internal logging format or exception handling strategy — use `logging-error-handling` for that. Do not use it when the security implication of error detail leakage is the primary risk — escalate to `security-privacy-gate`.

# Non-Negotiable Rules

- **Error codes are a compatibility contract.** Once a machine-readable error code is published to clients, it must remain stable. Clients branch on error codes in their error-handling logic. Changing a code name is a breaking change. Messages may be localized and refined; codes must not change.
- **Never return raw internal exceptions in API responses.** Stack traces, Java exception class names, Python tracebacks, SQL error messages, ORM entity names, internal field names, and third-party provider error bodies must never appear in client-facing error responses. This is OWASP API8:2023 (Security Misconfiguration) and CWE-209 (Information Exposure Through an Error Message). Wrap and translate all internal exceptions before returning.
- **Error codes are machine-readable URIs or namespaced strings, not human text.** Per RFC 7807, `type` is a URI that identifies the problem type. Clients that branch on `error.message === "User not found"` will break when the message is localized or rephrased. Clients that branch on `error.code === "USER_NOT_FOUND"` are resilient to message changes.
- **Retryability is declared, not inferred.** Every error code must declare whether it is retryable (client should retry automatically), non-retryable (client must not retry; re-submit requires human action), or conditionally retryable (idempotent requests only; with documented back-off strategy). 503 without `Retry-After` does not tell clients how to behave.
- **User-safe messages are separated from operator-diagnostic detail.** The user message says what the user can do: "The requested item is no longer available. Please refresh and try again." The operator diagnostic says what broke: "Cache key `product:123` returned MISS; upstream inventory service returned 500 after 3 retries." User messages go in the response body. Operator diagnostics go in structured logs, linked via correlation ID.
- **Authorization errors must not reveal resource existence.** A 404 for a resource the requester has no access to is safer than a 403 that confirms "the resource exists but you can't access it." Choose 404 over 403 when resource existence confirmation itself is sensitive (tenant isolation, user enumeration). Consistent behavior here is an OWASP API1:2023 (Broken Object Level Authorization) and OWASP API2:2023 concern.
- **Correlation IDs must be present and propagated.** Every error response must include a `traceId` or `requestId` that links the response to the server-side log entry. Without it, support engineers cannot find the log. The correlation ID must be in the HTTP response header (`X-Request-ID`, `X-Trace-Id`) and in the error response body. Propagate trace context via W3C TraceContext (`traceparent` header) for distributed tracing.
- **Validation errors include field-level detail.** A validation error must not return a single generic "Invalid input" message. It must return a structured list: which field failed, what the field's value was (if safe to echo), and what constraint was violated. Clients use this to highlight the specific form field. The field path must match the request body structure (JSON pointer or dotted path).

# Industry Benchmarks

Anchor error-code design on RFC 7807 / Problem Details, stable machine-readable codes, non-leaking client messages, compatibility of error semantics, and structured diagnostic correlation. Load [references/industry-benchmarks.md](references/industry-benchmarks.md) only when reviewing public API error semantics, SDK compatibility, or release documentation.

# Selection Rules

Select this capability when **error code semantics and error response contract design** are primary. Adjacent routing:

- Prefer `api-contract-design` when full operation contract (methods, status codes, request/response schemas) is primary.
- Prefer `dto-schema-design` when field-level validation error structure is being designed as part of a broader DTO.
- Prefer `logging-error-handling` when internal exception wrapping, logging format, and exception propagation strategy are primary.
- Prefer `security-privacy-gate` when error detail could leak sensitive data (tenant isolation, authentication bypass signals, PII).
- Prefer `observability` when distributed trace correlation and log-to-trace linking are primary.

# Risk Escalation Rules

Escalate when: an error response path could reveal whether a user account or resource exists (user enumeration attack surface); error detail could expose authentication secrets, session tokens, or private keys; a payment, financial, or healthcare transaction error could reveal account state to an unauthorized requester; an error from a downstream provider contains that provider's internal error details (which must be stripped and mapped); the error is from an authentication/authorization pathway where the response content affects security posture.

# Critical Details

Error responses are security surfaces, not just developer conveniences. Precision failures:

- **200 OK with error in body.** Some APIs return HTTP 200 with `{"success": false, "error": "..."}`. This breaks HTTP client libraries, load balancer health checks, CDN error caching, distributed trace error classification, and retry logic. Every error must use an appropriate 4xx or 5xx status code.
- **Branching on error messages.** Client code that does `if (error.message.includes("not found"))` breaks when the message is localized to French, reformatted, or made more specific. Machine-readable `error.code` or `error.type` URI is the stable surface for branching. Messages are for humans.
- **Information exposure via authorization errors.** `403 Forbidden` for `GET /users/987` tells the attacker "user 987 exists." `404 Not Found` tells them nothing. For systems where existence is sensitive (private posts, confidential records, per-tenant resources), return 404 for all unauthorized access, not 403. Document this pattern explicitly — it is counterintuitive to developers.
- **Retryable error without `Retry-After`.** A `503` without `Retry-After` causes clients to retry immediately (thundering herd) or not at all (if they give up). A `429` without `Retry-After` produces the same problem. Always include `Retry-After` (seconds or HTTP date) for any response that is retryable.
- **Idempotent retry without checking side effects.** A POST that creates an order returns 503. The client retries. The order was created on the first attempt; the second attempt creates a duplicate. Non-idempotent requests must use an `Idempotency-Key` header so the server can detect and deduplicate retries. Document this requirement in the error code definition.
- **Provider error body leakage.** The Stripe API, Twilio API, AWS SDK, or database driver returns its own error object. The backend catches it and serializes it directly to the response. This exposes provider API keys in error messages, internal DB query fragments, internal account identifiers, and API version details. Always catch + wrap + translate; never forward provider error bodies.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `return res.status(200).json({ error: "User not found" })` | Breaks HTTP error handling; load balancer sees healthy; not counted in error rate |
| Stack trace in 500 response body | CWE-209; attacker learns internal file paths, library versions, SQL query |
| `if (err.message === "User not found") { ... }` in client | Breaks on localization or rephrasing; no stable contract |
| `403 Forbidden` for all unauthorized resource access | Confirms resource existence; enables enumeration |
| `503` with no `Retry-After` | Thundering herd on retry; or client gives up; no guidance |
| `{"code": "ERR_001"}` — numeric code with no documentation | Client cannot understand meaning; error catalog not published |
| SQL error message forwarded in API response | Exposes table name, column names, DB engine version; SQL injection surface identified |
| Validation error: "Invalid input" (no field detail) | Client cannot highlight which field failed; usability failure |
| `Retry-After: 0` | Immediate retry storm; DDOS on recovering service |

# Failure Modes

- Client code branches on error message string; localization release breaks all error handling in client app.
- Stack trace returned in 500 response; attacker identifies Django/Flask version and targets known CVE.
- `403 Forbidden` for all protected resources; attacker enumerates valid user IDs via response code difference.
- Payment POST returns 503; client retries 3 times; customer charged 4 times; no idempotency key used.
- Downstream Stripe error object returned directly; Stripe secret key visible in response body of payment failure.
- Validation error returns "Invalid input" without field identification; form cannot highlight the failing field; user cannot complete task.
- Error codes refactored in sprint 12; `USER_NOT_FOUND` renamed to `ENTITY_NOT_FOUND`; all clients that branch on error code break silently (return wrong UI state).
- `429 Too Many Requests` without `Retry-After`; client library retries immediately at full rate; triggers secondary rate limit; cascading failure.
- Authentication error from OAuth provider forwarded verbatim; OAuth `client_secret` leak in access log via error response body.
- Support ticket: "I got an error." Engineer cannot find log because response contained no `traceId`; incident takes 4 hours to diagnose.

# Output Contract

Return an error catalog with:

- `error_code` (stable URI or namespaced string: `https://api.example.com/errors/INSUFFICIENT_FUNDS`)
- `category` (validation / auth / resource / business / capacity / server / gateway)
- `http_status` (per RFC 9110; with justification if non-obvious)
- `grpc_code` (google.rpc.Code; if gRPC surface exists)
- `user_safe_message` (what the user can do; no internal detail; localizable)
- `developer_detail_template` (logged server-side; linked via traceId; never in response body)
- `retryability` (not-retryable / retryable-after-delay / retryable-idempotent-only)
- `retry_guidance` (Retry-After strategy; back-off algorithm; max retry count)
- `idempotency_requirement` (required Y/N; Idempotency-Key header usage)
- `correlation_id_behavior` (traceId in response body; X-Request-ID in header; W3C traceparent propagated)
- `field_violations_format` (for validation errors: field path, constraint violated, rejected value)
- `authorization_posture` (404 vs 403 for protected resources; existence-leakage analysis)
- `localization_strategy` (message keys; translation process; code stable / message translatable)
- `governance` (who can add new error codes; where catalog is published; consumer notification process)
- `tests` (client branch test on code not message; no stack trace in response test; retryability behavior test; correlation ID present test)

# Quality Gate

The error catalog is complete only when:

1. All error codes are stable URIs or namespaced strings; not human-readable messages.
2. No raw exceptions, stack traces, SQL errors, or provider messages appear in any response path.
3. HTTP status codes match RFC 9110 semantics; no 200 OK with error in body.
4. Retryability declared per error code; retryable codes include `Retry-After` guidance.
5. Non-idempotent retryable operations document `Idempotency-Key` requirement.
6. User-safe messages contain no internal detail; developer diagnostics are in logs, linked by `traceId`.
7. Authorization error posture documented: 404 vs 403 per resource existence sensitivity.
8. Validation errors include field-level violations with field path and constraint description.
9. Error catalog is published (OpenAPI, internal wiki, or ADR); governance process defined.
10. Tests confirm: no stack trace in response; client can branch on code; traceId present; no provider error body leakage.

# Used By

- data-api-contract-changer
- backend-change-builder
- frontend-change-builder

# Handoff

Hand off to `api-contract-design` for operation-level contract; `dto-schema-design` for validation error response schema; `logging-error-handling` for internal diagnostic logging; `security-privacy-gate` for error detail leakage risk; `observability` for distributed trace correlation.

# Completion Criteria

The capability is complete when every error scenario has a **stable machine-readable code, a safe user message, an explicit retryability classification with retry guidance, a traceId-linked diagnostic path, no raw exception exposure, and a published error catalog** — with no error code renamed after release, no stack trace reachable from any error response, and no authorization error that leaks resource existence without explicit design intent.
