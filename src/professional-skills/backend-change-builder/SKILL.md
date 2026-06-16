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
- **Direct use still runs the runtime prompt flow.** When `backend-change-builder` is invoked directly and router reclassification is skipped, target-project engineering work must still clarify requirements before action, inspect relevant code/tests/config/docs before planning, name a TDD or validation signal before implementation, map each action to an owner skill and a different review skill, repair and re-review findings, and hand off with validation evidence, residual risk, and route/stage manifests when routed.
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
- **Run minimal-correctness review before adding backend machinery** — prefer existing validators, framework/database constraints, built-in retry/rate-limit/idempotency mechanisms, and feature-local functions before new generic managers, wrapper-only services, cache classes, schedulers, configuration switches, or dependencies.
- **Keep backend main flow readable** — validation, policy decisions, transactions, persistence, external calls, events, logging, and fallback handling must be named and separated enough that the use case can be reviewed without tracing infrastructure details.
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
- **Minimal correctness**: Standard library, platform/framework feature, database constraint, existing repository utility, or same-owner local code considered before new service/helper/dependency/config surface; any intentional shortcut has a ceiling and upgrade trigger.
- **Code clarity**: Main service/use-case flow is readable; complex conditions are named; boolean or mode switches are justified; pure policy is separated from side effects; cleanup and compatibility branches have owner and expiry.
- **Test coverage**: Unit tests for auth logic, validation logic, error paths; integration tests for transaction and idempotency behavior.

## Mode Matrix
Select one backend mode before implementation or review. Load [references/professional-modes.md](references/professional-modes.md) when the change is L3+, touches auth/data/async/release behavior, or the mode boundary is unclear.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| New backend capability | New endpoint, command handler, service, worker, repository, policy, or adapter. | Define trust boundary, ownership, transaction, idempotency, placement, and tests before code shape. | Existing controller/service/repository patterns inspected; validation/auth/transaction/test plan named. | `controller-api-implementation`, `service-business-logic`, `repository-persistence`, `implementation-structure-design`, `quality-test-gate` | Release/deep reliability gate unless the path is production-critical or async. |
| Modify existing backend logic | Existing service, repository, validator, job, or policy changes behavior. | Preserve compatible behavior while isolating the changed invariant. | Callers, tests, configs, error paths, and old behavior assertions inspected. | `code-clarity-maintainability`, `regression-testing`, `change-impact-analyzer` | New architecture review unless boundaries or dependencies move. |
| Bug fix | Defect, failing test, incident symptom, or local backend patch. | Verify cause, scan same pattern, add regression proof, avoid local-only patch. | Root cause evidence, pattern searched, related occurrences, regression test or rationale. | `failure-diagnosis`, `agent-execution-discipline`, `regression-testing` | Refactor beyond the defect boundary unless behavior preservation evidence exists. |
| Debugging diagnosis | Unknown root cause, flaky backend behavior, queue loss, inconsistent state, unexplained errors. | Diagnose before mutation; separate observed facts from hypotheses. | Logs/traces/tests/reproduction inspected; ruled-out hypotheses recorded. | `failure-diagnosis`, `observability`, `logging-error-handling` | Code mutation until cause is verified or a safe instrumentation change is justified. |
| AI generated backend code review | Generated service/helper/DTO/repository/job code or broad backend patch. | Find hallucinated APIs, missed reuse, wrong placement, hidden behavior changes, missing evidence. | Existing API/helper search, same-pattern scan, compile/test output, severity-classified findings. | `ai-code-review-refactor`, `implementation-structure-design`, `code-review` | Rewrite or expansion before review findings are classified. |
| Behavior-preserving refactor | Move/extract/split/rename backend code without intended behavior change. | Preserve public contract, transaction semantics, auth checks, errors, and side effects. | Before/after behavior, affected callers, tests, and deletion path. | `refactoring`, `code-clarity-maintainability`, `implementation-structure-design` | New behavior, new shared abstractions, or contract changes. |
| Performance/reliability fix | Latency, saturation, retry, queue, concurrency, N+1, pool, or job reliability risk. | Bound load, retries, concurrency, resource use, and observability. | Baseline, bottleneck, retry/idempotency/DLQ/metric evidence. | `idempotency-retry-design`, `async-job-design`, `reliability-observability-gate`, `profiling` | Cosmetic cleanup unrelated to measured risk. |
| Release/migration-sensitive backend change | Migration, config, feature flag, compatibility window, rollback, or irreversible mutation. | Ensure old/new version coexistence, rollback, audit, and operational readiness. | Expand/contract or rollout plan, config compatibility, rollback validation, owner. | `delivery-release-gate`, `data-migration-design`, `version-compatibility` | Contract cleanup until consumers and rollback are safe. |

## Proactive Professional Triggers
These triggers are hidden-risk escalators, not ordinary checklists. Load [references/proactive-triggers.md](references/proactive-triggers.md) for the full signal/risk/action/route/evidence contract.

- **Signal:** `resource_id`, `user_id`, `tenant_id`, account, order, invoice, or asset query lacks ownership or tenant filtering. **Hidden risk:** IDOR or tenant data leak. **Required professional action:** block local fix until object ownership and tenant boundary are traced. **Route to:** `permission-boundary-modeling`, `security-privacy-gate`. **Evidence required:** query/filter, policy check, denied-case test, same-pattern scan.
- **Signal:** retry, queue redelivery, cron, consumer, or webhook ingest lacks idempotency key, dedupe store, DLQ, or replay policy. **Hidden risk:** duplicate side effects, poison message, retry storm. **Required professional action:** design idempotent handling before accepting retry behavior. **Route to:** `idempotency-retry-design`, `message-queue-design`, `reliability-observability-gate`. **Evidence required:** key scope, dedupe storage, retry/DLQ policy, duplicate-delivery test.
- **Signal:** multi-step write crosses tables/services/events without transaction, compensation, saga, or partial-success handling. **Hidden risk:** inconsistent state. **Required professional action:** define atomic boundary or compensating recovery before code merge. **Route to:** `transaction-consistency`, `data-api-contract-changer`. **Evidence required:** transaction scope, rollback/compensation path, partial-failure test.
- **Signal:** catch block returns null/default/silent fallback without typed error, structured log, or correlation ID. **Hidden risk:** silent failure and invisible incident. **Required professional action:** replace with typed error/logging/metric behavior or justify safe fallback. **Route to:** `logging-error-handling`, `observability`. **Evidence required:** error taxonomy, correlated log field, metric/trace, negative test.
- **Signal:** controller/service/repository/adapter failures are caught, wrapped, retried, or returned without typed boundary semantics. **Hidden risk:** retryability, validation, permission, conflict, cancellation, dependency, and partial failures blur together. **Required professional action:** define the backend failure contract before closure. **Route to:** `failure-contract-design`, `logging-error-handling`. **Evidence required:** boundary translation map, retryability matrix, user-safe message, and negative tests.
- **Signal:** new collaborator, client, pool, provider, singleton, or global mutable dependency is constructed outside the composition root or per operation. **Hidden risk:** lifecycle leak, circular dependency, test override drift, or resource exhaustion. **Required professional action:** design dependency wiring and lifecycle. **Route to:** `dependency-wiring-lifecycle`, `implementation-structure-design`. **Evidence required:** dependency graph, lifecycle scope, construction/shutdown owner, config binding, and cycle check.
- **Signal:** mapper, getter, domain object, policy, or helper writes persistence, cache, events, files, logs, metrics, or external APIs. **Hidden risk:** hidden side effects and transaction ordering defects. **Required professional action:** trace data and side-effect flow before accepting placement. **Route to:** `data-side-effect-flow-tracing`, `transaction-consistency`. **Evidence required:** flow map, transaction boundary, cache source of truth, publish-after-commit decision, and idempotency/compensation.
- **Signal:** backend path scans, groups, sorts, dedupes, paginates, ranks, or joins unbounded collections. **Hidden risk:** wrong O(n squared) complexity, memory loss, stale hot-key assumptions, or load-all failure. **Required professional action:** require data structure and algorithm selection by input scale. **Route to:** `algorithm-data-structure-selection`, `solution-optimality-evaluation`. **Evidence required:** input size/distribution, complexity, memory budget, streaming/chunking decision, and benchmark/profile report.
- **Signal:** feature flag, mode/kind parameter, runtime config, or kill switch changes backend behavior without lifecycle governance. **Hidden risk:** config bypasses invariants or becomes a hidden strategy system. **Required professional action:** apply runtime configuration policy. **Route to:** `configuration-runtime-policy`, `cleanup-deletion-governance`. **Evidence required:** typed config, defaults, validation, owner, expiry, rollout/rollback, and cleanup path.
- **Signal:** new common/helper/utils file contains business words such as user, order, payment, tenant, invoice, permission, balance, or subscription. **Hidden risk:** shared utility pollution and boundary drift. **Required professional action:** prove reuse/placement or move logic to owned module. **Route to:** `implementation-structure-design`, `module-boundary-design`. **Evidence required:** reuse ladder, owner, dependency direction, deletion path.
- **Signal:** backend code adds a one-method service, generic manager/processor/helper, wrapper-only adapter, optional config flag, custom validator/parser/formatter, cache, rate limiter, retry helper, or new dependency before proving a current need.
  **Hidden risk:** backend validation, retry, cache, or dependency behavior can move into the wrong service owner and bypass transaction, auth, or failure-contract review.
  **Required professional action:** require a simplicity ladder, owner placement, and dependency review before accepting the new backend machinery.
  **Route to:** `minimal-correct-implementation`, `implementation-structure-design`, `package-dependency-management`.
  **Evidence required:** lower-cost option scan, current caller or scale evidence, validation command output, and shortcut ceiling if retained.
- **Signal:** service, controller, mapper, or repository passes API DTOs as domain objects, returns ORM/persistence models, or lets mapper code own business rules. **Hidden risk:** model boundary leak couples API, domain, and persistence behavior. **Required professional action:** map backend model boundaries before implementation closure. **Route to:** `model-boundary-mapping`, `data-api-contract-changer`. **Evidence required:** source/target model map, validation owner, null/default semantics, and mapping tests.
- **Signal:** new public DTO, response field, API error code, event payload, SDK type, or public export appears without compatibility, deprecation, or client behavior analysis. **Hidden risk:** known or unknown consumer contract break. **Required professional action:** run contract compatibility and consumer impact review before implementation closure. **Route to:** `consumer-impact-analysis`, `data-api-contract-changer`, `version-compatibility`. **Evidence required:** consumer list, schema/error docs, contract tests, migration note, telemetry, and rollback path.
- **Signal:** backend layer, repository, service, generated-code, import, export, or forbidden-dependency rule is documented but not checked in CI. **Hidden risk:** hidden dependency leaks and wrong backend dependency direction return after review. **Required professional action:** enforce the rule or create a staged report-only gate. **Route to:** `architecture-enforcement-tooling`, `module-boundary-design`. **Evidence required:** rule list, tool choice, CI command, failure example, generated-code exception, and owner.
- **Signal:** background task or async chain lacks ack/nack, retry, DLQ, replay, progress, or observability semantics. **Hidden risk:** lost work or invisible failure. **Required professional action:** require worker failure model before release. **Route to:** `async-job-design`, `reliability-observability-gate`. **Evidence required:** ack boundary, retry/DLQ metrics, replay procedure, failure test.
- **Signal:** permission, balance, ledger, subscription, asset, or irreversible operation lacks audit, re-authentication, approval, or rollback. **Hidden risk:** irreversible sensitive mutation can corrupt user state or lose rollback evidence. **Required professional action:** require security and release gate review before merge. **Route to:** `security-privacy-gate`, `delivery-release-gate`. **Evidence required:** audit record, re-auth/approval path, rollback or explicit irreversibility acceptance.

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
Apply when the change touches a performance-sensitive path, resource allocation model, or concurrency pattern. Answer the **Three-Challenge Rule** before finalizing: (1) why this approach over the alternatives, (2) is it the simplest sufficient design, (3) what is the strongest alternative and the specific cost that rejects it ("adds 40ms P99", "O(n²) at 500k records"). Then budget the performance dimensions — CPU, memory, network, disk, locks/contention, TPS/QPS, parallelism, concurrency, response latency — or mark each N/A with a one-line rationale.

Load [references/solution-optimality.md](references/solution-optimality.md) for the full backend performance-dimension matrix and additional considerations (GC pressure, Little's-Law pool sizing, back-pressure) when the change touches a performance-sensitive path. Method compiled from `solution-optimality-evaluation`.

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
- **Mode selected**: New-build / modify-existing / bug-fix / debugging-diagnosis / code-review / refactoring / performance-reliability / release-delivery, with the trigger signal that selected it.
- **Professional judgment**: backend decision made, plausible auth/consistency/idempotency/contract risks ruled out, and risks still possible.
- **Validation model**: Inputs, types, constraints, injection prevention — at trust boundary.
- **Authentication mechanism**: Token type, expiry, verification method.
- **Authorization model**: Role/permission check, object-level check per operation.
- **Trust boundary analysis**: HTTP/message/webhook/CLI boundary, caller identity source, tenant boundary, and untrusted fields rejected.
- **Authorization/tenant/object ownership analysis**: resource access path, ownership filter or policy check, denied cases, and same-pattern scan result.
- **Transaction boundaries**: Explicit commit/rollback scope, isolation level, compensating actions.
- **Transaction/partial-success analysis**: atomicity requirement, partial failure point, compensation or saga path, and rollback limitation.
- **Dependency wiring and lifecycle**: composition root, dependency graph, lifecycle scope, construction/shutdown owner, reusable client/pool policy, test override, and circular dependency check.
- **Failure contract**: typed failure taxonomy, controller/service/repository/adapter translation, retryability, fallback/degradation, safe user message, cause preservation, and negative-path tests.
- **Data and side-effect flow**: validation, mapping, policy, mutation, transaction, persistence, cache, event, external IO, ordering, publish-after-commit, idempotency, and compensation.
- **Algorithm/data-structure decision**: input size/distribution, complexity, memory budget, streaming/chunking, rejected alternatives, and benchmark/profile evidence when backend scale is material.
- **Configuration runtime policy**: typed config, safe defaults, validation/fail-fast behavior, feature flag lifecycle, mode/kind governance, rollout/rollback, and cleanup owner.
- **Idempotency design**: Key source, scope, deduplication window, expired-key behavior.
- **Idempotency/retry analysis**: retry source, duplicate-delivery behavior, dedupe storage, backoff, DLQ/replay plan when async.
- **Error model**: Error code taxonomy, HTTP status mapping, client-visible vs. server-log distinction.
- **Error/logging/observability analysis**: typed errors, structured logs, correlation ID, metric/trace signal, and alert/runbook implication.
- **Observability plan**: Log fields with correlation ID, metrics emitted, alert thresholds.
- **Concurrency analysis**: Race condition risk, locking strategy, ordering assumptions.
- **Boundaries inspected**: controllers, services, repositories, validators, jobs, mappers, configs, callers, API contracts, data boundaries, permission boundaries, and release boundaries inspected or explicitly skipped with reason.
- **Reuse and placement rationale**: Existing services/repositories/helpers inspected; reuse vs. new decision; function/class/file placement; public/private boundary; ownership; new imports and dependency direction.
- **Minimal Correctness Decision**: simplicity ladder result, deleted or rejected backend machinery, accepted direct/local implementation, and any shortcut ceiling with upgrade trigger.
- **Behavior preservation statement**: old behavior, public contract, error semantics, auth semantics, transaction semantics, and side effects preserved or intentionally changed.
- **Code clarity and maintainability**: main-flow readability, side-effect boundary, signature clarity, next-change location, and cleanup/deprecation plan.
- **Validation evidence**: commands run, outputs, same-pattern scan, regression/contract/integration coverage, and manual checks when tests are not possible.
- **Evidence limits**: what each backend check proves and what it does not prove about tenants, concurrency, async replay, rollback, load, or consumers.
- **Residual risk**: unverified concurrency, partial-write, DLQ, rollback, load, or consumer risk with owner.
- **Next gate/handoff**: next professional skill, capability, release gate, or explicit no-next-gate rationale.
- **Test obligations**: Unit tests for auth, validation, error paths; integration tests for transactions.

## Evidence Contract
Close a backend change only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: the selected mode, the authorization, consistency, idempotency, compatibility, or reliability rule the change rests on, and the OWASP API/RFC 7807/SRE benchmark it satisfies.
- **Files and boundaries inspected**: controllers, services, repositories, validators, jobs, mappers, configs, callers, API contracts, data boundaries, permission boundaries, trust boundaries, and release boundaries inspected or explicitly ruled out.
- **Placement rationale**: why each new service method, repository call, validator, mapper, job, adapter, or helper lives where it does, with dependency direction, ownership, shared/utils audit, and reuse ladder result (via `implementation-structure-design`).
- **Validation commands**: the literal unit, integration, regression, contract, migration, or validator commands run for auth, transaction, idempotency, error, retry, async, compatibility, and behavior-preservation paths, each with its outcome.
- **Backend judgment and evidence limits**: mode selected, professional decision, old behavior preserved or intentionally changed, what evidence proves, what it does not prove, and next gate/handoff.
- **Residual risk**: the concurrency, partial-write, DLQ, rollback, load, contract, or tenant-boundary path that remains untested or assumed, the owner, and the next gate or explicit acceptance.

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
16. Backend use-case flow remains readable; large services/functions, boolean traps, weak parameter bags, side-effect pollution, and stale compatibility branches are split or justified.

## Handoff
- **security-privacy-gate** — when authorization logic, PII handling, or sensitive data access requires adversarial review.
- **data-api-contract-changer** — when API response shapes, error codes, or pagination contracts are affected.
- **data-middleware-change-builder** — when schema, index, or query performance impact is significant.
- **reliability-observability-gate** — when SLO-affecting paths, async job reliability, or saturation risks are identified.
- **quality-test-gate** — when test coverage gaps for authorization, transactions, or concurrency are found.
- **domain-impact-modeler** — when business rule invariants, state machine transitions, or domain event emissions are affected.
- **testability-seam-design** — when backend tests need seams for time/randomness/external IO or risk private-helper coupling.
- **failure-contract-design** — when backend error states, retryability, fallback, or partial failure semantics are unclear.
- **dependency-wiring-lifecycle** — when dependency graph, reusable client lifecycle, service locator, or shutdown cleanup is unclear.
- **data-side-effect-flow-tracing** — when side effects may be hidden in mappers, policies, domain objects, getters, helpers, or repositories.
- **configuration-runtime-policy** — when runtime config, feature flags, mode/kind switches, or kill switches alter backend behavior.
- **model-boundary-mapping** — when DTOs, domain objects, persistence models, events, or mappers risk semantic leakage.
- **consumer-impact-analysis** — when backend public contracts, SDK types, events, exports, or response fields can affect downstream consumers.
- **architecture-enforcement-tooling** — when backend import, layer, export, generated-code, or forbidden-dependency rules need CI enforcement.
- **agent-execution-discipline** — when backend implementation evidence, verified cause, same-pattern scan, or handoff boundary is missing.

## Completion Criteria
Backend changes are safe to review and deploy when: all trust boundaries have validated input; all resource operations have server-enforced object-level authorization; all multi-step mutations have explicit transaction and compensation design; all retry paths are idempotent; error responses are machine-readable and non-leaking; structured logs carry correlation IDs; tests cover authorization, validation, error, and concurrency paths; and the implementation structure plan confirms reuse candidates, placement rationale, ownership, private/public boundary, shared utility audit, dependency direction, and test placement.
