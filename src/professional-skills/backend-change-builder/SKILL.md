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
- Agent-assisted backend fixes need evidence, verified cause, same-pattern scan, or reuse-and-placement rationale before acceptance.

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
- **Plan implementation structure before adding backend code** — inspect existing controllers, services, repositories, validators, mappers, jobs, helpers, and adapters before creating new functions, classes, files, or directories.
- **Agent backend fixes require execution discipline** — no local bug fix is accepted without same-pattern scan, test or validator evidence, and explicit boundary of changed backend behavior.

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
- **Implementation structure**: Existing services, repositories, validators, mappers, helpers, and adapters inspected; reuse vs. extension vs. composition vs. new code decision; function/class/file placement; public/private boundary; new imports and dependency direction.
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

## Solution Optimality Self-Check

*Compiled from foundation capability `solution-optimality-evaluation`. Apply to every backend change that touches a performance-sensitive path, resource allocation model, or concurrency pattern.*

**Three-Challenge Rule** — answer all three before finalizing any backend design:
1. **Why this approach?** State the concrete reason it satisfies the requirement better than the alternatives (not "it seemed natural").
2. **Is this the simplest sufficient design?** If a direct DB query replaces a cache + background job, use the simpler approach until profiling proves otherwise.
3. **What is the strongest alternative, and why is it rejected?** Name it. Reject it with a specific cost ("adds 40ms P99", "requires schema migration", "O(n²) at 500k records").

**Performance Dimension Checklist** — evaluate each or declare N/A with a one-line rationale:

| Dimension | Required Question | Backend-Specific Failure Mode |
|---|---|---|
| **CPU** | What is the time complexity (O notation)? Are there hot loops, precompile-required regexes, or unnecessary serialization per request? | O(n²) on a user-supplied list; regex evaluated per request without compilation; JSON re-serialized inside a loop |
| **Memory** | Are batch sizes bounded to prevent OOM? Is per-request heap allocation measured in GC-managed runtimes at target RPS? Does any global or long-lived structure lack eviction bounds? | Unbounded batch causing heap exhaustion; per-request allocation rate triggers GC pause spikes under load; in-memory map grows indefinitely |
| **Network** | Are N+1 database queries and N+1 HTTP fan-out patterns eliminated? Are bulk/batch calls used instead of per-item calls? | N+1 queries fetching related records in a loop; per-item HTTP POST instead of batch endpoint |
| **Disk** | Does the write pattern align with the storage engine's I/O model? Is WAL amplification acceptable? Are log volumes bounded? | Synchronous fsync per record; unbounded log verbosity at DEBUG level left in production |
| **Locks / Contention** | Is lock scope minimized (not held across I/O)? Is optimistic locking preferred for low-conflict cases? Is lock ordering consistent across all code paths (deadlock prevention)? | Pessimistic lock held across a remote API call; two code paths acquire locks in opposite order causing deadlock under concurrency |
| **TPS / QPS** | What is the throughput ceiling? Is pool size calculated via Little's Law (pool ≥ target RPS × avg service time in seconds)? Where does the first resource saturate? | Connection pool left at framework default (10) while target RPS requires 30+; no throughput ceiling defined for a new async job |
| **Parallelism** | Can background job work be safely partitioned? What is Amdahl's ceiling (1/(1−p)) given the sequential fraction? Is parallel coordination overhead justified at the expected batch size? | Parallelizing a job that is 70% sequential — maximum speedup is 3.3× regardless of thread count |
| **Concurrency** | Are all shared state accesses thread-safe? Is a TOCTOU race possible between the authorization check and mutation? Is a thundering herd risk addressed for cache-backed paths? | Time-of-check-to-time-of-use race on resource availability check; cache cleared on deploy causes thundering herd to the database |
| **Response Latency** | Are P95/P99 SLO targets defined and validated at expected concurrency? For fan-out to N services, is tail latency amplification modeled? | P99 undefined; fan-out to 5 downstream services at P99=60ms each — aggregate tail latency is substantially worse than per-service P99 |

**Additional Professional Considerations for Backend Code:**
- **GC pressure**: In JVM/Node.js/.NET runtimes, high per-request object allocation causes GC pause spikes that appear as P99 spikes only under load — invisible in local dev testing. Profile allocation rate per endpoint before accepting bulk-processing code.
- **Connection pool exhaustion — Little's Law**: Required pool size ≥ (target RPS) × (average service time in seconds). The default pool size (e.g., `pool: 10`) is almost never correct for production workloads. Validate with measurement, not assumption.
- **Back-pressure design**: Bounded queues with back-pressure are preferred over unbounded queues (OOM) or no queues (immediate rejection storms). Design the degradation mode explicitly.
- **Deferred optimization threshold**: If the current approach is acceptable only below a data volume or RPS threshold, document that threshold explicitly with a named owner — do not leave it as an undocumented time bomb.
- **Cognitive complexity**: Functions > 25 cognitive complexity must be decomposed before handoff. Clever code with a 3% CPU gain that requires 45 minutes to understand is not a net win.

## Risk Escalation Rules
- Escalate to `security-privacy-gate` when authorization logic is new, complex, or involves permissions, roles, or sensitive data access.
- Escalate to `data-api-contract-changer` when backend changes alter API response shapes, error codes, or pagination contracts.
- Escalate to `data-middleware-change-builder` when database schema, indexes, or query performance are significantly affected.
- Escalate to `reliability-observability-gate` when background job reliability, queue consumer behavior, or SLO-affecting paths change.
- Escalate when a distributed transaction or SAGA compensation pattern is introduced — the failure recovery model must be reviewed.
- Escalate when a change handles financial values, PII, health data, or legally sensitive records.
- Escalate when a background job has no dead-letter queue and failures would be silently lost.
- Escalate to `agent-execution-discipline` when the backend change is closed without evidence inventory, verified cause for a fix, or reuse-and-placement rationale for new service/helper structure.

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

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

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
- **Implementation structure**: Existing services/repositories/helpers inspected; reuse vs. new decision; function/class/file placement; public/private boundary; ownership; new imports and dependency direction.
- **Execution discipline evidence**: Commands run, outputs, same-pattern scan, reuse-and-placement rationale, residual risks, and validation results.
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
11. Existing backend functions, classes, services, repositories, validators, mappers, helpers, and adapters were checked before new code was added.
12. Every new backend function, class, or file has placement rationale and ownership.
13. No backend business logic is added to shared, common, or utils.
14. New imports respect module and layer dependency direction.
15. Agent-assisted backend changes include evidence, same-pattern scan for local fixes, and closure package.

## Handoff
- **security-privacy-gate** — when authorization logic, PII handling, or sensitive data access requires adversarial review.
- **data-api-contract-changer** — when API response shapes, error codes, or pagination contracts are affected.
- **data-middleware-change-builder** — when schema, index, or query performance impact is significant.
- **reliability-observability-gate** — when SLO-affecting paths, async job reliability, or saturation risks are identified.
- **quality-test-gate** — when test coverage gaps for authorization, transactions, or concurrency are found.
- **domain-impact-modeler** — when business rule invariants, state machine transitions, or domain event emissions are affected.
- **agent-execution-discipline** — when backend implementation evidence, verified cause, same-pattern scan, or handoff boundary is missing.

## Completion Criteria
Backend changes are safe to review and deploy when: all trust boundaries have validated input; all resource operations have server-enforced object-level authorization; all multi-step mutations have explicit transaction and compensation design; all retry paths are idempotent; error responses are machine-readable and non-leaking; structured logs carry correlation IDs; tests cover authorization, validation, error, and concurrency paths; and the implementation structure plan confirms reuse candidates, placement rationale, ownership, private/public boundary, shared utility audit, dependency direction, and test placement.
