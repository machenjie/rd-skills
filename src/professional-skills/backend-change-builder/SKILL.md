---
name: backend-change-builder
description: Guides backend correctness for product changes across input validation, authentication, authorization, object-level permission, transactions, idempotency, retry, logging, error model, concurrency, and async jobs.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Backend Change Builder

## Mission
Implement or review backend changes that preserve correctness, authorization integrity, consistency, idempotency, observable error semantics, concurrency safety, and operational transparency — because backend failures that are silent, partial, or irreversible are the most expensive failures in production.

## When To Use
- Service logic, endpoint handlers, command processors, or domain service methods are being added or modified.
- Authorization rules, object-level permissions, or tenant isolation is being changed.
- Transactional behavior, database writes, or data mutations are involved.
- Async workers, background jobs, or scheduled tasks are being built or changed.
- Retry logic, idempotency keys, or duplicate request handling is required.
- Logging, error codes, observability hooks, or alerting is added to a backend path.
- Concurrency, rate limiting, or shared-state access patterns are affected.

## Do Not Use When
- The change is purely frontend presentation work with no server-side logic.
- The change is read-only configuration or documentation with no behavioral path.
- API contract design (response shapes, versioning) is the primary concern — use `data-api-contract-changer` first.

## Non-Negotiable Rules
- **Always validate at trust boundaries** — every input that crosses a trust boundary (HTTP, message queue, webhook, CLI) must be validated for type, range, presence, and format before processing.
- **Always enforce authorization server-side** — client-supplied user IDs, resource IDs, and permission claims must be verified against the authoritative store, never trusted directly.
- **Object-level authorization (IDOR prevention)** — every resource fetch, update, and delete must verify that the authenticated principal owns or has explicit permission to that specific object, not just the resource class.
- **Never leak PII, secrets, or internal state in error responses** — error messages visible to clients must be generic; detailed errors go to structured server-side logs only.
- **Idempotency for all mutating operations** — any operation that can be retried by a client, queue consumer, or cron must be safe to execute multiple times with the same effect.
- **Explicit transaction boundaries** — write operations that must succeed or fail atomically must be wrapped in an explicit transaction; never rely on implicit ORM behavior.
- **Partial-success is a first-class failure mode** — if a multi-step write can partially succeed, define and test the compensation or rollback behavior explicitly.
- **Structured logging with correlation** — every request must carry a correlation/trace ID through all log entries; logs must not contain plaintext secrets, passwords, or full PII.
- **All non-trivial backend logic requires unit tests** — including auth logic, validation logic, error paths, retry behavior, and concurrency edge cases.

## Industry Benchmarks
- **OWASP API Security Top 10**: API1 (Broken Object Level Authorization), API2 (Broken Authentication), API3 (Broken Object Property Level Authorization), API8 (Security Misconfiguration) — all address backend authorization failures.
- **OWASP Top 10**: A01 (Broken Access Control), A02 (Cryptographic Failures), A03 (Injection) — input validation and server-side enforcement.
- **The Twelve-Factor App**: Factor III (Config), Factor XI (Logs) — structured logging, no hardcoded secrets, environment-based config.
- **Google SRE Book**: Chapter 8 (Release Engineering), Chapter 13 (Emergency Response) — operational clarity through structured error models and runbooks.
- **RFC 7807 Problem Details for HTTP APIs**: Standard format for machine-readable error responses — `type`, `title`, `status`, `detail`, `instance`.
- **Saga Pattern (Richardson)**: For distributed transactions — choreography vs. orchestration, compensation transactions, idempotent participants.
- **Structured Logging Standards (OpenTelemetry)**: Log correlation via `trace_id` and `span_id` for distributed request tracing.

### Backend Risk Classification Matrix

| Operation Type | Key Risks | Required Controls |
|---|---|---|
| Data-mutating endpoint | IDOR, partial write, idempotency | Object authz, transaction, idempotency key |
| External webhook ingest | Replay, spoofing, poison messages | Signature verify, idempotency, DLQ |
| Background / async job | Duplicate execution, partial success | Idempotency, at-least-once handling, compensation |
| Privileged admin action | Authorization bypass, audit gap | Re-authentication, immutable audit log |
| External API call | Timeout, retry amplification | Bounded retry, circuit breaker, idempotency |
| Bulk data operation | Partial failure, performance | Batch size limits, progress tracking, rollback |

## Technical Selection Criteria
Evaluate backend changes across these dimensions:
- **Input validation**: Schema, type, range, presence, encoding, injection prevention — at the service boundary, not inside business logic.
- **Authentication**: Token type (JWT/session/API key), expiry, revocation, and verification mechanism.
- **Authorization model**: Role-based (RBAC) or attribute-based (ABAC) — with explicit object-level check per resource operation.
- **Tenant isolation**: Multi-tenant services must filter by tenant identity at the query level, not application logic.
- **Transaction design**: Explicit `BEGIN/COMMIT/ROLLBACK` boundaries; optimistic vs. pessimistic locking decision; isolation level.
- **Idempotency design**: Idempotency key scope (client-provided or server-generated), deduplication window, storage medium.
- **Retry and backoff**: Bounded retry count, exponential backoff with jitter, idempotency on all retry paths.
- **Async job design**: Exactly-once vs. at-least-once semantics, failure acknowledgment, DLQ routing, retry policy.
- **Error model**: Error codes, HTTP status mapping, client-visible message (generic), server-log message (detailed), correlation ID.
- **Observability**: Logs (structured + correlated), metrics (latency, error rate, saturation), traces (distributed trace propagation).
- **Concurrency**: Race condition analysis, lock scope, optimistic concurrency control, queue ordering guarantees.
- **Test coverage**: Unit tests for auth logic, validation logic, error paths; integration tests for transaction and idempotency behavior.

### Decision Tree: Authorization Check Required?

```
Is the operation reading or mutating a resource that belongs to a user or tenant?
├── Yes → Require object-level authorization check (IDOR prevention)
│   └── No explicit check → Block: missing authorization
Is the operation callable by multiple roles?
├── Yes → Require role-based permission check before any resource access
│   └── Roles undefined → Escalate to security-privacy-gate
Is the caller identity supplied by the client (e.g., user_id in body)?
├── Yes → NEVER trust it — always resolve from authenticated session/token
Is the operation irreversible (delete, financial write, permission grant)?
├── Yes → Require re-authentication or explicit confirmation token
All checks pass → Proceed with implementation
```

## Risk Escalation Rules
- Escalate to `security-privacy-gate` when authorization logic is new, complex, or involves permissions, roles, or sensitive data access.
- Escalate to `data-api-contract-changer` when backend changes alter API response shapes, error codes, or pagination contracts.
- Escalate to `data-middleware-change-builder` when database schema, indexes, or query performance are significantly affected.
- Escalate to `reliability-observability-gate` when background job reliability, queue consumer behavior, or SLO-affecting paths change.
- Escalate when a distributed transaction or SAGA compensation pattern is introduced — the failure recovery model must be reviewed.
- Escalate when a change handles financial values, PII, health data, or legally sensitive records.
- Escalate when a background job has no dead-letter queue and failures would be silently lost.

## Critical Details
- **IDOR is the most common high-severity API vulnerability**: Every `GET /api/resource/:id`, `PUT`, `DELETE` must check `resource.owner_id == authenticated_user.id` (or equivalent) after fetching the resource — not before.
- **Idempotency key storage**: Idempotency keys require a dedicated index, appropriate TTL, and behavior for expired-key re-use (reject, allow, or treat as new).
- **N+1 query pattern**: Backend code that fetches a list and then queries per item causes exponential database load at production scale — always batch or eager-load.
- **Optimistic locking**: Use version columns or ETags for update operations on shared resources to prevent lost-update race conditions.
- **Correlation ID propagation**: Every inbound request should receive or generate a trace/correlation ID that propagates through all outbound calls, logs, and error responses.
- **Structured error codes**: Error responses must include a machine-readable code (e.g., `INSUFFICIENT_FUNDS`, `RESOURCE_NOT_FOUND`) alongside the HTTP status — human messages are UI concerns.
- **Config via environment**: Secrets, connection strings, and feature flags must come from environment config, not hardcoded defaults in source code.
- **Boolean traps in function signatures**: `createUser(id, isAdmin, isActive, isSuspended)` — use named parameter objects; boolean positional parameters are a common source of inverted authorization bugs.

### Anti-Examples

| Backend Pattern | Problem | Corrected Approach |
|---|---|---|
| `if user.role == "admin": return resource` | Missing object-level authorization | Fetch resource, check `resource.owner_id == user.id` or explicit permission |
| `user_id = request.body["user_id"]` | Client-supplied identity trusted | `user_id = request.auth.user_id` from verified session/token |
| `retry 5 times immediately` | No backoff, amplifies upstream load | Exponential backoff with jitter: 1s, 2s, 4s, 8s, 16s |
| `catch (e) { return null }` | Silent failure, no log, no error propagation | Log with trace ID, return typed error, never swallow |
| `SELECT * FROM orders WHERE id = :id` (no tenant check) | Tenant isolation breach | `WHERE id = :id AND tenant_id = :tenant_id` |

## Failure Modes
- **Missing object-level authorization (IDOR)**: User A fetches or modifies User B's data by guessing resource IDs — a top-ranked API security vulnerability globally.
- **Non-idempotent retry duplicates effects**: A payment retry creates a duplicate charge because the initial operation had no idempotency key.
- **Partial write leaves inconsistent state**: Steps 1 and 2 of a multi-step write succeed; step 3 fails; no compensation runs — data is permanently corrupted.
- **Sensitive data in logs**: A `user.password`, `card_number`, or `api_secret` appears in structured logs and is shipped to a log aggregation service.
- **Background job silently fails**: A job fails after the ACK, leaving the message acknowledged but unprocessed — no DLQ, no alert, no visibility.
- **N+1 database queries**: A list endpoint performs one query per item in the result set — tolerated in development, catastrophic at production load.
- **Tenant data leak in multi-tenant service**: A missing `tenant_id` filter in a query returns records from multiple tenants to a single caller.
- **Config secret hardcoded in source**: A development-only API key is committed to source control, later used by accident in production.
- **Race condition on shared state**: Two concurrent requests increment the same counter without locking, causing a lost-update and incorrect final value.

## Output Contract
Return a backend implementation plan or review with:
- **Validation model**: Inputs, types, constraints, injection prevention — at trust boundary.
- **Authentication mechanism**: Token type, expiry, verification method.
- **Authorization model**: Role/permission check, object-level check per operation.
- **Transaction boundaries**: Explicit commit/rollback scope, isolation level, compensating actions.
- **Idempotency design**: Key source, scope, deduplication window, expired-key behavior.
- **Error model**: Error code taxonomy, HTTP status mapping, client-visible vs. server-log distinction.
- **Observability plan**: Log fields with correlation ID, metrics emitted, alert thresholds.
- **Concurrency analysis**: Race condition risk, locking strategy, ordering assumptions.
- **Test obligations**: Unit tests for auth, validation, error paths; integration tests for transactions.

## Quality Gate
1. Every trust boundary has explicit input validation covering type, range, presence, and injection prevention.
2. Object-level authorization is enforced server-side for every resource operation — IDOR prevention verified.
3. All multi-step write operations have explicit transaction boundaries and compensation plans.
4. All mutating operations that can be retried have idempotency design.
5. Error responses are machine-readable, use generic client messages, and include correlation IDs.
6. Logs are structured, contain correlation IDs, and contain no plaintext secrets or PII.
7. Background jobs have DLQ routing and failure alerting.
8. Unit tests cover authorization logic, validation logic, and error paths.
9. Concurrency race conditions are analyzed and mitigated for shared-state operations.
10. No hardcoded secrets, API keys, or connection strings in source code.

## Handoff
- **security-privacy-gate** — when authorization logic, PII handling, or sensitive data access requires adversarial review.
- **data-api-contract-changer** — when API response shapes, error codes, or pagination contracts are affected.
- **data-middleware-change-builder** — when schema, index, or query performance impact is significant.
- **reliability-observability-gate** — when SLO-affecting paths, async job reliability, or saturation risks are identified.
- **quality-test-gate** — when test coverage gaps for authorization, transactions, or concurrency are found.
- **domain-impact-modeler** — when business rule invariants, state machine transitions, or domain event emissions are affected.

## Completion Criteria
Backend changes are safe to review and deploy when: all trust boundaries have validated input; all resource operations have server-enforced object-level authorization; all multi-step mutations have explicit transaction and compensation design; all retry paths are idempotent; error responses are machine-readable and non-leaking; structured logs carry correlation IDs; and tests cover authorization, validation, error, and concurrency paths.
