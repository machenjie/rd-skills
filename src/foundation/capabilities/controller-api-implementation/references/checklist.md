# Controller API Implementation Checklist

## Scope And Boundaries

- Identify route, method, operation owner, API contract source, and generated artifact source when present.
- Record middleware/auth chain, request context source, correlation id source, validator/schema path, service boundary, mapper boundary, and error catalog.
- Parse transport inputs without embedding business decisions, persistence calls, transaction control, or provider calls.
- Delegate workflow, transactions, domain decisions, object authorization, and idempotency execution outside the controller.
- Reject raw request binding, controller-owned ownership decisions, repository calls, domain-object responses, and raw exception responses.

## Transport Responsibilities

- Invoke trusted validation before service invocation and map validation failures to stable field-level errors.
- Extract authentication context from trusted middleware/session/token state, not body/query-supplied identity.
- Forward subject, tenant, scopes/roles, correlation id, idempotency key, and validated command/query to the use case.
- Map service results to response DTO, status code, headers, content type, pagination, and rate-limit or retry metadata.
- Convert known errors to client-safe RFC 7807/9457 responses and hide stack traces, SQL/provider details, secrets, PII, tenant ids, and internal policy names.
- Enforce content negotiation, size/page limits, multipart/streaming limits, and idempotency header syntax at the transport boundary when applicable.

## Evidence And Tests

- Confirm repository graph shows controller delegates business logic, persistence, authorization decisions, transactions, and provider calls.
- Reconcile project memory, old API docs, generated controllers, copied handlers, and prior validation against current contract and route wiring.
- Add controller unit tests with mocked service for success, validation failure, auth context extraction, status code mapping, error body format, headers, and service-not-called invalid cases.
- Add or reference contract/security/integration evidence for API shape, object authorization, idempotency behavior, content negotiation, and large payload behavior when those risks are selected.
- Map each controller responsibility to validation evidence, what the evidence proves, what it does not prove, residual risk, owner, and next gate.
