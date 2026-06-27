---
name: service-business-logic
description: Defines application service orchestration for use cases, transactions, repositories, policies, and domain operations while avoiding pass-through and god services.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "38"
changeforge_version: 0.1.0
---

# Mission

**Design application services as precise use-case orchestrators** that coordinate authorization, transaction scope, domain operations, repository calls, events, external effects, retries, and compensation without becoming pass-through wrappers, god services, duplicate domain-rule engines, or hidden infrastructure adapters.

# When To Use

Use this capability when a change adds or modifies an application service, command/query handler, workflow service, use-case object, or backend orchestration path; when logic is split across controller, service, repository, domain, event, or external integration layers; when authorization order, transaction ownership, event timing, idempotency, retry, or compensation is unclear; when a service is growing into a god service; or when repository graph, project memory, or prior execution suggests an existing service pattern that must be source-confirmed before reuse.

# Do Not Use When

Do not use this capability to define domain invariants themselves (use `domain-logic-implementation`), transport/API mapping (use `controller-api-implementation`), persistence contracts (use `repository-persistence`), distributed workflow/job design (use `async-job-design`), or retry/saga mechanics in depth (use `idempotency-retry-design` and `transaction-consistency`). Do not add a service layer around simple CRUD unless it protects a real use-case boundary, policy, transaction, test seam, or future extraction that is explicitly justified.

# Stage Fit

Use during backend implementation planning, coding, testing, code-review, repair, and release-readiness when application-layer orchestration is the primary decision. In planning, name the use case, actor, authorization order, transaction boundary, domain authority, repository participation, side-effect sequencing, idempotency, compensation, and validation evidence before code shape is accepted. In review, reject pass-through wrappers, god services, data access before authorization, domain rule duplication, framework-coupled services, external calls inside transactions, pre-commit event publishing, and stale graph/memory claims not confirmed against current source and tests.

# Non-Negotiable Rules

- **One service owns one coherent use case or workflow.** A generic `OrderService` with unrelated place/cancel/ship/return/invoice methods is a god service. Split by use case when actors, policies, transaction boundaries, or side effects differ.
- **Authorization happens before protected data access.** The service must establish actor/resource scope before fetching sensitive records, or explicitly document the non-leaking lookup pattern.
- **Transaction boundaries are explicit.** State which repository/domain operations run inside the transaction, which effects are outside it, and what rolls back or compensates on failure.
- **External effects do not hide inside database transactions.** Payment, email, webhook, file, queue, cache, and third-party calls need idempotency, timeout, retry, and compensation decisions outside or alongside the consistency boundary.
- **Domain invariants stay in the domain authority.** Services orchestrate calls such as `order.cancel()`; they do not duplicate lifecycle, price, entitlement, terminal-state, or ownership rules as service `if` branches.
- **Events publish after consistency is established.** Use after-commit publication or an outbox when consumers depend on source state. Never publish integration events before the write they describe is durable.
- **Pass-through services need a boundary reason.** If a service only calls a repository, collapse it or document the architectural boundary, current consumers, expected extraction, and test seam.
- **Services stay framework and infrastructure neutral.** Constructor-injected ports are acceptable; HTTP request objects, ORM sessions, framework containers, raw DB exceptions, and vendor clients in the service interface are boundary leaks unless explicitly justified as local convention.
- **Read services stay side-effect-free unless the side effect is named and routed.** Query handlers should not mutate state, emit domain events, or acquire write dependencies without explicit command/query boundary review.
- **Graph, memory, and trajectory evidence are inputs, not proof.** Reuse existing service patterns only after current callers, imports, tests, transaction owners, and validation freshness are inspected.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Command use case | State-changing request, domain transition, write repository, event, external effect. | Authorization-first orchestration, transaction scope, domain operation, event/effect timing. | Actor/resource/action, domain authority, repositories, transaction map, failure and idempotency plan. | `domain-logic-implementation`, `transaction-consistency`, `idempotency-retry-design` | Controller-owned business logic. |
| Query use case | Read path, details page, report lookup, list/search service. | Permission-aware read scope, bounded query, mapping, no write side effects. | Access scope, repository/query method, DTO/projection owner, pagination/ordering, no side-effect proof. | `repository-persistence`, `dto-schema-design` | Hidden write in read path. |
| Workflow orchestrator | Multi-step process, async handoff, outbox, event, job, external provider. | Durable step boundaries, retry/compensation, status source, operator visibility. | Step map, consistency boundary, idempotency key, compensation, event/job timing. | `async-job-design`, `data-side-effect-flow-tracing`, `reliability-observability-gate` | Long-running sync transaction. |
| Service decomposition | God service, unrelated methods, too many dependencies, merge conflicts. | Split by use case/domain boundary while preserving behavior and callers. | Method inventory, actor/policy/transaction differences, caller map, migration/test plan. | `implementation-structure-design`, `refactoring`, `module-boundary-design` | Cosmetic split without behavior seam. |
| Boundary exception | Pass-through service, transaction script, framework-first convention, legacy bridge. | Decide whether the shortcut is simpler and contained or hides missing orchestration. | Local convention, boundary reason, consumer list, expiry/review trigger, residual risk. | `minimal-correct-implementation`, `architecture-impact-reviewer` | Abstract service for every repository. |
| Existing pattern reuse | Repository graph, project memory, or prior trajectory suggests a service pattern. | Confirm freshness before reuse and reject stale or unsafe patterns. | Current source/tests/docs inspected, accepted/rejected pattern, validation freshness, changed-service delta. | `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis` | Copying old service shape blindly. |

# Industry Benchmarks

Anchor against DDD Application Service, Clean Architecture Use Case Interactor, Fowler Service Layer and Transaction Script, CQRS command/query separation, Hexagonal Ports and Adapters, Unit of Work, Transactional Outbox, SRE failure/timeout readiness, and framework service conventions that keep lifecycle management separate from business orchestration. Keep this body focused on routing, evidence, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed matrices, sequencing patterns, compensation examples, graph/memory/trajectory coupling, and anti-pattern review.

# Selection Rules

Select this capability when application-layer orchestration is primary: authorization order, transaction scope, domain operation sequencing, repository coordination, event publication, external effect timing, idempotency, retry, or compensation. Route elsewhere when rule authority is primary (`domain-logic-implementation`), persistence interface is primary (`repository-persistence`), transport mapping is primary (`controller-api-implementation`), distributed workflow mechanics are primary (`async-job-design` / `idempotency-retry-design`), or macro layer assignment is primary (`layered-architecture-design`).

# Proactive Professional Triggers

- **Signal:** Service reads a protected record before authorization. **Hidden risk:** existence leak, timing side channel, or object-level permission bypass. **Required professional action:** move to scope-first authorization or document non-leaking lookup. **Route to:** `authentication-authorization`, `security-privacy-gate` when sensitive. **Evidence required:** actor/resource/action scope, query order, denied test.
- **Signal:** External API, payment, email, file, webhook, queue, or cache effect occurs inside a DB transaction. **Hidden risk:** rollback cannot undo external side effect. **Required professional action:** move effect boundary, add outbox/idempotency/compensation. **Route to:** `transaction-consistency`, `idempotency-retry-design`, `data-side-effect-flow-tracing`. **Evidence required:** transaction map, effect timing, retry and compensation path.
- **Signal:** Service checks lifecycle, price, entitlement, or status invariant directly. **Hidden risk:** duplicated business rule drifts from domain authority. **Required professional action:** call domain operation/policy and map typed outcome. **Route to:** `domain-logic-implementation`, `state-machine-modeling`. **Evidence required:** rule owner, rejected service branch, domain denied-case test.
- **Signal:** Service has many unrelated public methods or constructor dependencies. **Hidden risk:** god service with hidden coupling and broad regression blast radius. **Required professional action:** inventory use cases and split by actor/policy/transaction boundary. **Route to:** `implementation-structure-design`, `refactoring`. **Evidence required:** method/caller map, preserved behavior tests, rollout path.
- **Signal:** Repository graph or project memory is used to justify service placement. **Hidden risk:** stale convention, removed policy, or old transaction behavior copied forward. **Required professional action:** inspect current callers/imports/tests, compare the pattern to the changed service, and mark stale evidence. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** accepted/rejected reuse map, inspected path list, validation command or report, and freshness limit.
- **Signal:** Service test starts full web framework or real infrastructure for local orchestration logic. **Hidden risk:** application layer is coupled to delivery/infrastructure and tests become slow or skipped. **Required professional action:** define constructor-injected ports, service-level tests, and a separate adapter integration proof. **Route to:** `test-strategy`, `quality-test-gate`. **Evidence required:** unit test output, mock/fake boundary, integration test or report for real adapters, and residual unverified seam.

# Risk Escalation Rules

Escalate when a service orchestrates payments, subscriptions, billing, inventory, entitlements, tenant/object permissions, irreversible writes, external providers, multi-repository transactions, queues, file operations, customer notifications, audit trails, or operational recovery. Escalate when a command is retryable without idempotency, a read path can leak existence, a service emits events before commit, or a pass-through wrapper hides missing domain/repository ownership.

# Critical Details

- **Application service is orchestration, not rule ownership.** It translates a use-case command into authorization, domain method calls, repository persistence, event capture, and effect sequencing.
- **Authorization-first means more than a method call.** The policy must be able to decide safely before sensitive data is fetched, or the service must use a scoped query that cannot reveal inaccessible records.
- **Transaction map is a design artifact.** Name participating repositories, domain operations, outbox/event writes, external effects, rollback behavior, and which failures are retryable or terminal.
- **Outbox is often the safer event boundary.** If consumers depend on source state, write the event record in the same transaction and publish asynchronously after commit.
- **Query handlers need service discipline too.** A read service still needs permission scope, bounded repository query, projection owner, pagination, and evidence that no hidden write side effects occur.
- **Framework annotations do not define a service boundary.** `@Service`, `@Injectable`, or equivalent lifecycle metadata is not proof of use-case cohesion, dependency direction, or testability.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 selection, stage fit, routing, evidence, output, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete service plan, command/query handler, transaction map, service decomposition, or side-effect sequence. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when detailed service-type matrices, sequencing examples, compensation patterns, graph/memory/trajectory coupling, review questions, or anti-pattern analysis is needed. Use [examples/example-output.md](examples/example-output.md) only when output shape is unclear. Do not load references for pure routing or trivial wording changes where the inline output contract and quality gate are enough.

# Failure Modes

- **God service blast radius:** unrelated methods accumulate in one service, so a change to cancellation risks placement, invoicing, returns, and fulfillment workflows.
- **Authorization-after-fetch leak:** repository fetch runs before actor/resource scope is proven, letting timing or not-found behavior reveal protected records.
- **Rollback cannot undo provider effect:** payment, webhook, or email succeeds while the DB transaction rolls back, leaving source state and external reality inconsistent.
- **Duplicated domain guard drift:** service `if` branches copy lifecycle or entitlement rules and diverge when the domain model adds a state or policy.
- **Pre-commit event ghost:** integration event is emitted before durable commit, so consumers observe missing or later-rolled-back source data.
- **Query-side hidden write:** query handler updates view counts, audit rows, or cache state without command semantics, tests, or transaction review.
- **Framework-bound service tests:** orchestration tests require full web framework startup, become slow or skipped, and stop proving service behavior directly.
- **Stale memory reuse:** project memory copies an old transaction or event timing pattern after repositories, policies, or outbox behavior changed.

# Output Contract

Return a service logic plan with:

- `mode_selected` (command use case / query use case / workflow orchestrator / service decomposition / boundary exception / existing pattern reuse)
- `service_scope` (use case name, actor, command/query, owning module, included workflow, excluded responsibilities, and local convention)
- `source_evidence` (current controllers/handlers/jobs, services, repositories, domain objects, policies, events, tests, repository graph, project memory, execution trajectory, and freshness limits)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for each reused service pattern, transaction pattern, policy order, event timing, test seam, or validation result)
- `service_responsibility` (what the service coordinates and what it must not own)
- `inputs_outputs` (command/query object, validation boundary, result type, typed failures)
- `authorization_order` (policy or scoped-query decision; proof it precedes protected data access or non-leaking rationale)
- `transaction_boundary` (operations inside transaction, outside transaction, rollback behavior, isolation/lock concern, Unit of Work owner)
- `domain_operations` (domain methods/policies called, invariant owner, expected domain exceptions/results)
- `repository_operations` (repositories used, read/write role, transaction participation, not-found/filtered semantics)
- `external_effects` (provider/file/cache/queue/email/payment calls, timing, timeout, idempotency key, retry, compensation)
- `emitted_events` (domain/integration event, outbox or after-commit timing, consumer consistency assumption)
- `failure_handling` (validation, denial, not found, conflict, timeout, duplicate, partial failure, retry exhaustion, compensation)
- `service_level_tests` (unit with ports/mocks/fakes, narrow integration tests, denied/invalid/partial failure/idempotency cases)
- `changed_service_to_validation_map` (each service method, policy order, transaction boundary, domain call, repository call, event/effect, failure path, and test seam mapped to validator/test or residual risk)
- `handoff_boundaries` (what belongs to domain logic, repository persistence, controller/API, transaction consistency, idempotency/retry, async job, security, reliability, or quality gate)
- `evidence_limits` (what was not inspected or run: full call graph, real DB, external provider, production permissions, concurrency, generated clients, framework startup, or CI tests)

# Evidence Contract

Close a service-business-logic output only when it names selected mode, service scope, boundaries inspected, current source evidence, graph/memory/trajectory reuse judgment, service responsibility, input/output contract, authorization order, transaction boundary, domain and repository operations, external effects, emitted events, failure handling, service-level tests, changed-service-to-validation map, validation commands or report artifacts with exit codes, what evidence proves, what evidence does not prove, handoff boundaries, residual risk, validation freshness, and evidence limits. A generic "put logic in a service" or "use clean architecture" statement is not sufficient evidence.

# Benchmark Coverage

Improved service outputs reject common weak patterns: god service buckets, pass-through wrappers without boundary reason, data access before authorization, service-owned domain invariants, external effects inside transactions, pre-commit event emission, query-side writes, framework-coupled services, mocked-only confidence for persistence effects, and stale graph/memory reuse. Detailed benchmark anchors, sequencing examples, compensation patterns, and anti-pattern matrices belong in references so the body stays efficient.

# Routing Coverage

Route here when concrete application-service orchestration, command/query handler responsibility, service decomposition, transaction sequencing, authorization-first order, repository/domain coordination, event timing, or external side-effect handling is primary. Hand off when the primary concern is layer assignment (`layered-architecture-design`), domain invariant implementation (`domain-logic-implementation`), repository contract (`repository-persistence`), API/controller mapping (`controller-api-implementation`), distributed retry/saga (`idempotency-retry-design` / `transaction-consistency`), async jobs (`async-job-design`), security policy (`authentication-authorization`), reliability operations (`reliability-observability-gate`), or executable tests (`quality-test-gate`).

# Quality Gate

The service design is complete only when:

1. Selected mode, service scope, source evidence, and graph/memory/trajectory reuse judgment are explicit.
2. Each service represents one coherent use case, query, workflow, or justified boundary exception.
3. Authorization or scoped lookup precedes protected data access.
4. Transaction boundary, Unit of Work owner, rollback behavior, and outside-transaction effects are explicit.
5. External effects have timing, timeout, idempotency, retry, and compensation decisions.
6. Domain invariants are delegated to domain entities, value objects, policies, or domain services.
7. Repository calls use repository contracts and do not leak ORM/query/session mechanics into service interfaces.
8. Events are emitted after commit or via outbox when consumer consistency matters.
9. Query services remain side-effect-free or explicitly route side effects as commands/jobs.
10. Pass-through services have a documented boundary reason, owner, consumers, and review trigger.
11. Service tests run without full web framework startup for pure orchestration behavior.
12. Denial, invalid state, not-found/filtered, partial failure, retry/idempotency, and compensation paths have tests or residual risk.
13. Each changed service method, policy order, transaction boundary, domain call, repository call, event/effect, and failure path maps to validation evidence or named residual risk.
14. Handoff boundaries and evidence limits are explicit so service evidence is not over-claimed as domain, repository, API, transaction, security, reliability, or full integration proof.

# Used By

- backend-change-builder
- domain-impact-modeler

# Handoff

Hand off to `domain-logic-implementation` for invariant placement; `repository-persistence` for data access contracts and persistence proof; `authentication-authorization` for policy and object-scope decisions; `transaction-consistency` and `idempotency-retry-design` for retry, locking, outbox, compensation, and distributed consistency; `async-job-design` for long-running or event-driven workflows; `quality-test-gate` for executable service validation; and `reliability-observability-gate` when operator visibility, SLOs, or recovery are part of the workflow.

# Completion Criteria

The capability is complete when **each service has a bounded use-case or query responsibility, authorization-safe data access, explicit transaction and side-effect sequencing, domain-invariant delegation, repository-boundary discipline, idempotency/compensation decisions for retryable effects, service-level validation mapping, and evidence limits that prevent orchestration guidance from being over-claimed as full integration proof**.
