# Service Business Logic Benchmarks And Patterns

Use this reference when `service-business-logic` output needs more detail than the `SKILL.md` body should carry efficiently. Keep the main body focused on selection, evidence, output, and gates; use this file for benchmark anchors, service-type matrices, sequencing patterns, compensation examples, graph/memory/trajectory coupling, review questions, and anti-pattern review.

## Contents

- Benchmark Anchors
- Service Responsibility Matrix
- Command Service Sequence
- Query Service Discipline
- Transaction And Side-Effect Matrix
- Decomposition And Boundary Exceptions
- Test Evidence Matrix
- Graph, Memory, And Trajectory Coupling
- Review Questions
- Anti-Patterns To Reject
- Handoff Boundaries

## Benchmark Anchors

- DDD Application Service: coordinates domain objects and repositories, but does not own domain rules.
- Clean Architecture Use Case Interactor: represents one business use case and depends inward on domain contracts.
- Fowler Service Layer: defines application operations and transaction boundaries; Transaction Script remains valid for simple workflows.
- CQRS: command handlers change state; query handlers return data without side effects.
- Hexagonal Architecture: services use ports; adapters own databases, HTTP clients, queues, files, and framework APIs.
- Unit of Work: transaction ownership belongs to the use case, not hidden repository commits.
- Transactional Outbox: write event records with source state, publish after commit for reliable delivery.
- SRE failure readiness: external effects need timeout, retry, idempotency, and observable terminal states.
- Test pyramid: service orchestration should have fast unit tests with ports and targeted integration tests for real seams.

## Service Responsibility Matrix

| Service type | Owns | Must not own | Required evidence |
| --- | --- | --- | --- |
| Command use-case handler | Authorization, domain operation sequencing, transaction, persistence, events/effects. | Domain invariant logic or transport mapping. | Use case, actor, policy, transaction map, side-effect plan. |
| Query handler | Permission-scoped read, projection/DTO coordination, pagination/order. | Writes, events, external effects. | Scoped query, projection owner, no-side-effect proof. |
| Workflow orchestrator | Step state, async handoff, compensation, status source. | Long synchronous transaction across providers. | Step map, retry/idempotency, operator visibility. |
| Policy application service | Calls a domain/application policy as part of use case. | Pure rule ownership when domain owns the policy. | Policy owner, inputs, typed failure, test seam. |
| Anti-corruption service | Translates between legacy/external model and current use case. | Business rule mutation hidden in adapter translation. | Translation map, rejected direct model leak, contract tests. |
| Pass-through boundary | Stable facade for a known boundary. | Empty layer added only for ceremony. | Consumers, boundary reason, expiry/review trigger. |

## Command Service Sequence

```text
1. Accept command/query object, not raw transport request.
2. Validate boundary format and safe defaults.
3. Authorize actor/resource/action or use a non-leaking scoped lookup.
4. Start transaction or Unit of Work when state changes require consistency.
5. Load required aggregates through repositories.
6. Invoke domain methods/policies that own invariants.
7. Persist changed aggregates and write outbox/domain event records when needed.
8. Commit transaction.
9. Execute external effects after commit, or publish through outbox.
10. Compensate, retry, or mark terminal state on external failure.
11. Return typed result and failure mapping owner.
```

Deviations are allowed only when the local architecture has a documented convention and the residual risk is named.

## Query Service Discipline

| Query concern | Strong treatment | Failure if omitted |
| --- | --- | --- |
| Authorization | Scope query by actor/tenant/role before protected data access. | Existence leak or object-level permission bypass. |
| Pagination/order | Require bounded limit and stable ordering. | OOM, unstable UI, duplicate/missing rows. |
| Projection | Return DTO/read model intentionally, not ORM entity. | Persistence leak and lazy-loading behavior. |
| Consistency | State primary/replica/stale-read semantics. | Users see stale or contradictory state. |
| Side effects | Keep absent or route to command/job. | Hidden writes in read path. |
| Not found/filtered | Map absence, no-access, deleted, and filtered outcomes deliberately. | Caller infers sensitive existence or retries incorrectly. |

## Transaction And Side-Effect Matrix

| Operation | Inside transaction | Outside transaction | Notes |
| --- | --- | --- | --- |
| Domain state transition | Usually yes. | No, unless pure preview. | Domain rejects invalid state before save. |
| Repository save | Yes for consistent write. | Rare, only explicit eventual consistency. | Avoid repository-owned hidden commits. |
| Outbox record write | Yes. | No. | Source state and event record commit together. |
| Event publish to broker | No. | Yes, after commit or via outbox publisher. | Avoid consumers seeing missing source state. |
| Payment/provider call | Usually no. | Yes, with idempotency and compensation. | Cannot roll back provider side effect. |
| Email/webhook/file/cache | Usually no. | Yes, with retry/terminal behavior. | Cache invalidation may be after commit or outbox-driven. |
| Audit log | Depends on audit contract. | Depends on durability requirement. | Security audit may need same transaction or append-only adapter. |

## Decomposition And Boundary Exceptions

| Situation | Prefer | Evidence |
| --- | --- | --- |
| Methods differ by actor/policy/transaction/effect. | Split into use-case handlers. | Method inventory, caller map, tests. |
| Simple CRUD with no meaningful invariant. | Transaction Script or direct handler per local convention. | Simplicity rationale and public behavior test. |
| Service has many constructor dependencies. | Split by use case or introduce domain policy/port. | Dependency grouping and responsibility map. |
| Pass-through service isolates bounded context or future extraction. | Keep with explicit boundary reason. | Consumers, review trigger, ownership. |
| Legacy service cannot be split safely now. | Contain and add owner/expiry. | Residual risk, tests, follow-up. |

## Test Evidence Matrix

| Risk | Minimum evidence | Stronger evidence |
| --- | --- | --- |
| Authorization order | Denied actor test proves no protected record access or scoped lookup. | Repository spy/contract plus integration permission test. |
| Domain invariant delegation | Service test asserts domain operation called or domain result mapped. | Domain denied-case tests plus service mapping test. |
| Transaction boundary | Unit test of Unit of Work participation or integration rollback test. | Real DB rollback and outbox atomicity test. |
| External effect compensation | Failure simulation proves compensation/retry/terminal state. | Provider sandbox contract and idempotency replay test. |
| Event timing | Test proves event/outbox after durable state. | Consumer integration test under delayed publish. |
| Query side effects | Test or review proves read handler has no write dependencies. | Architecture/import rule forbids write dependencies in query package. |
| Service decomposition | Existing behavior regression tests for moved methods. | Caller contract tests and same-pattern scan. |

## Graph, Memory, And Trajectory Coupling

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current controllers, services, domain objects, repositories, policies, events, jobs, and tests were inspected. | Graph proximity is treated as proof that the service owns a use case. |
| Project memory | Prior service pattern names unchanged files, owners, transaction behavior, and validation freshness. | Memory predates service split, policy change, repository rewrite, event timing change, or framework migration. |
| Execution trajectory | Service tests, architecture checks, or validators ran after final orchestration edit. | Evidence predates final edit or covers only one happy path. |
| Previous incidents | Incident maps to current code path and has reproduced behavior. | Incident is anecdotal or from retired workflow. |
| Existing tests | Tests cover success, denial, invalid state, partial failure, and effect timing as relevant. | Tests require full framework startup for pure service behavior or mock real persistence effects only. |

Strong outputs state which graph or memory evidence was accepted, rejected, or left unknown.

## Review Questions

1. What exact use case, actor, command/query, and module does the service own?
2. What responsibilities are explicitly outside this service?
3. What authorization or scoped lookup occurs before protected data access?
4. Which domain methods or policies own invariants, and which service branches were rejected?
5. Which repositories participate in the transaction, and who owns the Unit of Work?
6. Which external effects happen after commit, and what idempotency/compensation exists?
7. Which events are domain events, outbox records, or integration events, and when are they published?
8. Which failure paths are validation, denial, not found, conflict, timeout, duplicate, partial failure, retry exhaustion, or compensation?
9. Which service tests prove orchestration without starting a web framework?
10. Which graph, memory, trajectory, production, provider, DB, or CI evidence remains unverified?

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| God service with unrelated methods. | Hidden coupling and broad regression blast radius. | Split by use case or document contained legacy risk. |
| Repository fetch before authorization. | Existence leak and unauthorized data access. | Authorize scope first or use non-leaking scoped query. |
| External call inside DB transaction. | Rollback cannot undo provider side effect. | Move effect out, add idempotency and compensation. |
| Service duplicates domain status guards. | Rule drift from domain authority. | Invoke domain operation and map typed result. |
| Event publish before commit. | Consumer observes missing source state. | Publish after commit or use outbox. |
| Query handler writes "small" side effect. | CQRS boundary breaks silently. | Route write to command/job or document exception. |
| Framework container required for service unit test. | Application layer coupled to delivery mechanism. | Constructor-inject ports and test service directly. |
| Pass-through service by default. | Ceremony without behavior protection. | Collapse or state boundary reason and review trigger. |
| Project memory copied without source check. | Stale transaction/policy/event behavior persists. | Inspect current source and validation freshness. |

## Handoff Boundaries

- Use `domain-logic-implementation` for invariant, transition, value object, calculation, and domain policy authority.
- Use `repository-persistence` for repository contracts, mapping, not-found behavior, transactions at repository boundary, and real DB proof.
- Use `controller-api-implementation` for transport parsing, DTO validation, status mapping, and response shape.
- Use `authentication-authorization` and `permission-boundary-modeling` for object/action/scope policy design.
- Use `transaction-consistency`, `idempotency-retry-design`, and `data-side-effect-flow-tracing` for locks, retries, outbox, compensation, and distributed side effects.
- Use `async-job-design` and `message-queue-design` for long-running workflows and durable job/event processing.
- Use `quality-test-gate` for executable service-level validation and validation freshness.
- Use `reliability-observability-gate` when operator visibility, SLOs, alerts, dashboards, or recovery paths are in scope.
