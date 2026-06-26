---
name: controller-api-implementation
description: Defines controller responsibilities for transport parsing, validation handoff, auth context, response mapping, and error boundaries without core business logic.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "37"
changeforge_version: 0.1.0
---

# Mission

Implement API controllers as **thin transport adapters** — parsing and validating input at the trusted boundary, extracting and forwarding authentication context, delegating all business decisions to the application layer, mapping results to contract-compliant response shapes, and enforcing error boundaries that prevent internal implementation details from leaking to clients — so that the controller is independently testable, contract-aligned, and free of business logic.

# When To Use

Use this capability when a change adds or modifies: HTTP handler functions or route handlers, gRPC server method implementations, RPC handler dispatch, controller class methods, request body / query parameter / path variable parsing, validation invocation at the API boundary, authentication/authorization context extraction and propagation, response DTO mapping (service result → HTTP response), HTTP status code assignment, error response transformation, controller middleware wiring (correlation IDs, logging context, rate-limit headers), streaming or multipart response handling, or controller-level idempotency header processing.

# Do Not Use When

Do not use this capability to design business rules, domain invariants, use-case logic, transaction orchestration, or data access patterns — those belong in the service or domain layer. Do not use it to design the API contract shape itself — use `api-contract-design`. Do not use it to implement authorization policies — use `authentication-authorization`; the controller only extracts and forwards identity context. Do not use it for integration or e2e test design — use `integration-testing`.

# Stage Fit

- **Discovery / intake** - identify the route/operation, contract source, trust boundary, auth context, affected clients, and existing controller conventions before implementation.
- **Implementation / coding** - keep the controller thin: parse, validate, extract context, delegate, map response, and map errors.
- **Code review** - verify no business logic, persistence access, object-level authorization shortcut, domain-object response, or raw exception leakage entered the controller.
- **Testing / release** - map controller responsibilities to unit/contract/integration checks, validation freshness, and client-safe error evidence.

# Non-Negotiable Rules

- **Controllers are transport adapters, not business logic hosts.** The controller's job: (1) parse and deserialize input; (2) validate structure and types at the API boundary; (3) extract auth context (user identity, scopes, tenant) from the request; (4) invoke the correct use case or service method; (5) map the result to the response shape; (6) map errors to appropriate status codes and error bodies. Nothing else.
- **No business logic in controller branches.** A controller `if` branch that makes a product decision ("if user is premium, return extended data") is business logic. It belongs in the service/domain layer. Controllers may branch only on: input validation outcome, error type mapping, content negotiation, or transport-specific protocol differences.
- **Input validation fires at the trusted boundary, every time.** All externally-supplied values are untrusted until validated: path variables, query parameters, request body, headers, multipart fields. Validation includes: structural shape (schema), type coercion, required fields, length/range constraints, format (email, UUID, date), and allowlist enumeration. Never assume a value is safe because it came from a known client.
- **Auth context is extracted, not decided.** The controller extracts `userId`, `tenantId`, `scopes`, and `roles` from the validated bearer token / session. It does NOT decide whether the user is authorized — it passes the identity context to the service/policy layer. Object-level authorization (BOLA/IDOR) checks run in the service layer where the resource is fetched — not in the controller.
- **Response shape must match the API contract.** Status codes, response body structure, required fields, Content-Type, pagination envelope, and error body format must match the OpenAPI spec or equivalent. Controllers map internal service results to DTOs; they do not return persistence objects, internal domain objects, or ORM entities directly.
- **Error boundaries prevent internal details from leaking.** Controller error handlers catch: validation errors → 400/422, not-found → 404, authentication errors → 401, authorization errors → 403, conflict → 409, unprocessable domain errors → 422, unexpected internal errors → 500. Raw exception messages, stack traces, SQL errors, internal IDs, and service topology must never reach the response body.
- **Correlation and tracing context is captured at entry.** Every request has a correlation ID (from `X-Request-ID` header or generated if absent), propagated to the logger and to downstream calls as a trace context. Controllers are the canonical entry point for structured logging context.
- **Idempotency keys are validated at the controller boundary.** If the operation is non-idempotent (payment, booking), the controller validates the `Idempotency-Key` header format and forwards it to the service; the service checks for duplicate execution.
- **Content negotiation follows the contract.** `Content-Type` and `Accept` headers are validated; 415 Unsupported Media Type is returned for unrecognized content types; 406 Not Acceptable for unsupported accept types.
- **Current graph and contract evidence are required.** Controller guidance must cite current route wiring, contract source, middleware/auth path, service boundary, prior API decisions, and validation commands; stale memory or inferred conventions are not enough.

# Industry Benchmarks

Anchor against: Clean Architecture, Hexagonal Architecture, DDD Application Service, OWASP API Security Top 10, OWASP Input Validation, RFC 7807/RFC 9457 Problem Details, RFC 9110 HTTP Semantics, REST/API design guidelines, Google API Design Guide, and OpenAPI/proto contracts. Use these as boundary and response-shape checks, not as substitutes for the target project's current route graph and contract source.

# HTTP Status Code Decision Matrix

| Situation | Correct status | Wrong (common) | Notes |
| --- | --- | --- | --- |
| Input validation failure | **400** Bad Request or **422** Unprocessable Entity | 200 with error in body | 422 for semantic failures (valid JSON, invalid meaning); 400 for malformed |
| Resource not found | **404** Not Found | 200 `{data: null}` | Never leak existence of auth-gated resources; return 403/404 consistently |
| Unauthenticated request | **401** Unauthorized | 403 Forbidden | 401 = no/invalid credentials; must include `WWW-Authenticate` |
| Authenticated but unauthorized | **403** Forbidden | 401, 404 | 404 may be safer than 403 for existence-leaking resources |
| Resource already exists / conflict | **409** Conflict | 400, 500 | 409 for idempotency key collision, duplicate unique key, version conflict |
| Successful creation | **201** Created + `Location` header | 200 | 201 must include `Location` pointing to new resource |
| Successful async enqueue | **202** Accepted | 200, 201 | 202 = enqueued; body should include status-check URL |
| No content response | **204** No Content | 200 `{}` | DELETE, PATCH with no body; `204` must not have response body |
| Rate limited | **429** Too Many Requests | 503 | Must include `Retry-After` header |
| Unexpected internal error | **500** Internal Server Error | leaking stack trace | Log full context server-side; return generic Problem Details body |

# Controller Layer Responsibilities

| Responsibility | Controller? | Service/Domain? |
| --- | --- | --- |
| Parse path variables, query params, body | ✅ Yes | No |
| Validate input structure / format | ✅ Yes (invoke validator) | No (not re-validate) |
| Extract userId/tenantId from JWT | ✅ Yes | No |
| Decide if user can access resource | No | ✅ Yes |
| Apply business rule (`order.cancel()`) | No | ✅ Yes |
| Execute DB query | No | ✅ Yes (repository) |
| Map service result → response DTO | ✅ Yes | No |
| Choose HTTP status code | ✅ Yes (from error type) | Provide error type |
| Format error body (RFC 7807) | ✅ Yes | No |
| Log correlation ID / trace context | ✅ Yes (entry point) | Propagate context |
| Idempotency key header validation | ✅ Yes (format check) | ✅ Yes (deduplicate) |

# Error Mapping Decision Tree

```
Service throws / returns error
├─ ValidationError (schema/input)     → 400 or 422; Problem Details; field-level errors
├─ NotFoundError                       → 404; Problem Details; do NOT reveal existence of auth-gated resource
├─ UnauthorizedError (not authed)      → 401; WWW-Authenticate header
├─ ForbiddenError (authed, no access)  → 403; minimal detail
├─ ConflictError (idempotency/version) → 409; include conflicting resource ref if safe
├─ DomainRuleViolation                 → 422; machine-readable error code in Problem Details `type`
├─ RateLimitError                      → 429; Retry-After header
├─ ExternalDependencyTimeout           → 503 or 504; Retry-After if applicable
└─ Unexpected / uncaught               → 500; log full context; return generic body WITHOUT internal details
```

# Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `if (user.plan === 'premium') { return extendedData; }` in controller | Business logic in transport layer; duplicated in every controller that checks plan; not unit-testable without full service wiring |
| `return res.json(dbRow)` — returning ORM entity directly | Leaks internal field names, relation IDs, timestamps, DB schema; contract breaks on schema change |
| `catch (e) { return res.status(500).json({ error: e.message, stack: e.stack }) }` | Stack trace and internal messages exposed to clients; information disclosure (OWASP API9) |
| Authorization: `if (userId === resource.ownerId)` in controller | BOLA check in controller; bypassed by any path that skips the controller; must be in service layer with fresh DB read |
| No validation; pass raw body to service | SQL injection, NoSQL injection, unexpected type coercion, oversized payload DoS |
| `return res.status(200).json({ error: "Not found" })` | Client error signalled with 200; breaks any HTTP-aware middleware, retry logic, monitoring |
| Calling repository directly from controller | Repository is infrastructure; controller bypasses service layer; business rules skipped |

# Selection Rules

Select this capability when **transport-layer implementation** is the main decision. Adjacent routing:

- Prefer `api-contract-design` when the API shape (operations, request/response schema) is still being designed.
- Prefer `service-business-logic` when use-case orchestration or domain transitions are primary.
- Prefer `authentication-authorization` when authorization policy design is the main concern.
- Prefer `error-code-design` when designing the error taxonomy and machine-readable error codes.
- Prefer `integration-testing` for testing controller + service + persistence wired together.

# Proactive Professional Triggers

Use this capability proactively, even when the request does not ask for controller design:

- **Signal:** a diff adds or modifies an HTTP handler, route method, gRPC method, RPC dispatcher, middleware endpoint, streaming endpoint, or multipart endpoint. **Hidden risk:** business rules, persistence, object authorization, or response contracts can leak into the transport adapter. **Required professional action:** map the route to thin-controller responsibilities and reject non-transport work from the controller. **Route to:** `controller-api-implementation`, `service-business-logic`, `api-contract-design`, and `quality-test-gate`. **Evidence required:** route path, service method, forbidden responsibilities, contract reference, and controller test plan.
- **Signal:** repository graph shows controller code calling repositories, domain mutators, external providers, transaction managers, pricing/rule functions, or policy decisions directly. **Hidden risk:** transport layer bypasses service invariants and makes tests slow or incomplete. **Required professional action:** inspect caller/callee graph and move decisions to the owning service/domain/policy layer. **Route to:** `repository-graph-analysis`, `service-business-logic`, `domain-logic-implementation`, and this capability. **Evidence required:** graph paths, rejected controller calls, service boundary, and behavior-preservation test.
- **Signal:** project memory, old API docs, generated controllers, copied handlers, or previous examples are reused as implementation proof. **Hidden risk:** stale conventions can preserve wrong status codes, missing validation, auth bypasses, or contract drift. **Required professional action:** compare memory against current OpenAPI/proto, middleware chain, tests, and route wiring. **Route to:** `project-memory-governance`, `execution-trajectory-analysis`, `validation-broker`, and this capability. **Evidence required:** source date, accepted/rejected assumptions, current contract, validation command, and unknowns.
- **Signal:** controller response maps raw service errors, ORM/domain objects, stack traces, SQL errors, internal IDs, privileged fields, or inconsistent status codes. **Hidden risk:** internal details leak, clients break, and monitoring/retry behavior misclassifies failures. **Required professional action:** require DTO mapping, Problem Details/error taxonomy, allowlisted fields, and client-safe error mapping. **Route to:** `error-code-design`, `input-validation`, `security-privacy-gate`, and this capability. **Evidence required:** response schema, error map, redaction/allowlist, negative tests, and contract result.
- **Signal:** endpoint handles auth context, tenant scope, destructive writes, idempotency keys, large payloads, rate-limit headers, or public unauthenticated access. **Hidden risk:** controller-level shortcut can create BOLA, duplicate side effects, DoS, or broken retry semantics. **Required professional action:** validate transport-only handling and route policy/deduplication/resource checks to service and specialist gates. **Route to:** `authentication-authorization`, `idempotency-retry-design`, `performance-budgeting`, and this capability. **Evidence required:** auth context fields, idempotency header rule, max payload/page policy, rate-limit headers, and service-layer authorization proof.

# Reference Loading Policy

- **L1:** Use only this `SKILL.md` for routing or rejecting business logic in a controller when the route and contract are obvious.
- **L2:** Load `references/checklist.md` when drafting or reviewing a real controller implementation plan, transport boundary review, or controller unit-test plan.
- **L3:** Load `examples/example-output.md` when the expected output contract shape is unclear or a concise user-facing plan is needed.
- **L4:** Pair with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when the controller decision depends on route wiring, middleware/auth chain, generated code, prior API decisions, tests, command output, or validation freshness.
- **L5:** Pair only selected specialist gates: `api-contract-design`, `input-validation`, `error-code-design`, `authentication-authorization`, `idempotency-retry-design`, `security-privacy-gate`, `performance-budgeting`, or `integration-testing`; do not load unrelated references for a simple thin-controller rejection.

# Risk Escalation Rules

Escalate when: the endpoint handles authentication or token exchange (OAuth flows, session creation); the controller implements object-level authorization (risk: BOLA); the endpoint performs destructive writes (deletion, financial transaction, bulk operation); the endpoint processes sensitive PII, PHI, or payment data; the endpoint is on a public API with no authentication; a status code or error body change may break contract-verified consumers; the endpoint uses streaming, multipart, or chunked transfer encoding with large payload limits; the controller bypasses middleware for any reason.

# Critical Details

Controllers are the first trust boundary. Every security, performance, and contract regression passes through here:

- **Never re-use domain objects as response DTOs.** Domain objects encode business invariants and internal state. Returning them directly exposes internal structure to clients. Always map through an explicit response DTO or serializer. Changing a domain object for a business reason must not silently change the API contract.
- **Validation error messages must be stable and parseable.** Clients implement retry and UX logic based on validation error bodies. Field-level errors (`{"field": "email", "code": "INVALID_FORMAT", "message": "..."}`) are more useful than free-text. RFC 7807 `type` URI as machine-readable error code.
- **Controller tests should not require real databases.** A controller test should mock the service layer and test: routing, input parsing, validation response, status code mapping, error body format, auth context extraction. If the test requires a real DB, business logic has leaked into the controller.
- **Rate limiting and throttling headers are controller-layer concerns.** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After` are returned at the controller/middleware layer, not deep in service logic.
- **OWASP Mass Assignment (API3).** When binding a request body to an object, explicitly allowlist which fields are bindable. `Object.assign(entity, req.body)` without allowlisting allows clients to overwrite privileged fields (e.g., `isAdmin`, `balance`).
- **Streaming and large responses.** For endpoints returning large datasets, the controller should enforce maximum page sizes, not delegate that decision to the caller. Unbounded result sets → OOM, timeout, DoS.
- **gRPC controller specifics.** gRPC server method implementations follow the same thin-adapter principle: parse request message, validate, extract metadata (auth headers), invoke service, map response message, return appropriate gRPC status code (`INVALID_ARGUMENT`, `NOT_FOUND`, `PERMISSION_DENIED`, `INTERNAL`).

# Failure Modes

- Business rule duplicated in controller and service; diverges silently when one is updated.
- ORM entity returned directly; internal field names and relations exposed; contract breaks on schema refactor.
- Stack trace returned in 500 response; internal service topology discoverable by clients.
- Authorization check in controller only; route called via internal service-to-service path; BOLA bypassed.
- Raw `req.body` passed to DB query without validation; SQL/NoSQL injection possible.
- Status 200 returned for all errors with error field in body; monitoring, alerting, retries, and contract tests blind to errors.
- Validation called once in controller but service called again with unvalidated path params; second injection surface.
- `Content-Type: application/json` not set on response; client parses error as HTML 500 page from reverse proxy.
- Controller test spins up full service + DB; slow test suite; business logic tested at wrong layer.
- Missing `Location` header on 201 response; clients cannot retrieve created resource without additional design.
- Idempotency key not validated; duplicate payment processed; no deduplication window.
- Mass assignment: `user.set(req.body)` overwrites `role`, `isAdmin`, `creditBalance`.

# Output Contract

Return a controller implementation plan with:

- `route_or_operation` (HTTP method + path or gRPC service + method; OpenAPI operationId)
- `boundaries_inspected` (route wiring, middleware/auth chain, contract source, service boundary, generated code, tests, and skipped boundaries)
- `graph_memory_execution_validation` (current repository graph, project memory, API docs, generated artifacts, test output, and validation evidence accepted or rejected with freshness limits)
- `request_parsing` (path variables, query params, headers, body schema reference)
- `validation_handoff` (validator invoked, schema reference, validation error response shape)
- `auth_context_extraction` (claims extracted: userId, tenantId, scopes; forwarded to service as)
- `service_invocation` (service class + method, input DTO, expected return type)
- `response_mapping` (result DTO mapping; response body schema; status codes per outcome)
- `error_mapping` (error type → HTTP status code → Problem Details body; per error class)
- `idempotency` (header validated; forwarded to service; deduplication window)
- `logging_context` (correlation ID source; structured log fields attached at entry)
- `forbidden_responsibilities` (explicit list of what this controller must not do)
- `test_plan` (unit tests: routing, validation, status codes, error bodies — all with mocked service)
- `contract_reference` (OpenAPI operationId or proto method reference this controller implements)
- `controller_to_validation_map` (each controller responsibility mapped to unit, contract, integration, security, or validation-broker evidence)
- `evidence_limits` (not-inspected routes, stale API docs, generated-code uncertainty, skipped integration tests, or unresolved policy owner)

# Quality Gate

The controller implementation passes only when:

1. Controller has no business logic, domain invariants, or persistence access.
2. All external inputs are validated at the API boundary with schema reference.
3. Auth context is extracted and forwarded; authorization is performed in the service layer.
4. Every response shape and status code matches the API contract spec.
5. Error responses use RFC 7807 Problem Details; no internal exception messages or stack traces leak.
6. Correlation / trace context is captured at entry and propagated.
7. Controller is unit-testable with mocked service (no DB required).
8. Object-level authorization is not in the controller.
9. Request body binding uses explicit field allowlisting (no mass assignment).
10. Large collection responses enforce a maximum page size.
11. Repository graph confirms the controller delegates business logic, persistence, authorization decisions, transactions, and provider calls outside the transport adapter.
12. Project memory, generated controllers, old API docs, and copied handlers are accepted or rejected against current contract and route wiring.
13. Controller-to-validation map covers success, validation failure, auth context extraction, client-safe errors, status codes, DTO mapping, content negotiation, and forbidden responsibilities.
14. Evidence limits and residual risk state what was not verified and which specialist gate owns it.

# Evidence Contract

The controller plan must cite `boundaries_inspected`, validation commands or artifacts, what evidence proves, what evidence does not prove, residual risk, and next handoff gate. Controller evidence proves transport parsing, validation handoff, auth context extraction, service delegation, response mapping, and error boundaries for the inspected route only; it does not prove service authorization, domain invariants, persistence correctness, or full API compatibility unless those gates were selected and verified. Missing route graph, contract source, middleware/auth path, generated-code freshness, or validation evidence blocks completion.

# Benchmark Coverage

Architecture and HTTP standards calibrate responsibility boundaries and response semantics. Approval requires current project evidence: route graph, contract source, DTO mapping, middleware/auth chain, controller tests, and client-safe error validation.

# Routing Coverage

When selected by a router, report which adjacent capabilities were loaded or intentionally skipped: `api-contract-design`, `input-validation`, `error-code-design`, `authentication-authorization`, `idempotency-retry-design`, `service-business-logic`, `integration-testing`, `security-privacy-gate`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker`.

# Used By

- backend-change-builder
- data-api-contract-changer

# Handoff

Hand off to `service-business-logic` for use-case orchestration; `authentication-authorization` for authorization policy; `error-code-design` for error taxonomy; `api-contract-design` for contract shape; `integration-testing` for end-to-end behavior testing.

# Completion Criteria

The capability is complete when **the controller can be reviewed as a pure transport adapter** — input is parsed and validated, identity is extracted and forwarded, business decisions happen in the service layer, all responses match the API contract, current graph/memory/execution evidence supports the boundary, and no internal exception detail, domain object internals, or business rules are visible in the controller code.
