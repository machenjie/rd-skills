---
name: repository-persistence
description: Defines repository persistence boundaries, domain mapping, transaction expectations, and prevents ORM-specific objects from leaking across domain boundaries.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "40"
changeforge_version: 0.1.0
---

# Mission

**Define repository interfaces as persistence boundaries that expose domain-oriented contracts, hide storage mechanics, and prevent ORM-specific objects, query builders, and lazy-loading behavior from leaking into domain and application logic** — so that the persistence layer can change its storage implementation, ORM version, or database technology without requiring changes to the domain model or application services.

# When To Use

Use this capability when: a new entity type needs a persistence access point; an existing repository needs a new query method and the semantics (not-found behavior, consistency level, pagination contract) are unclear; a service is directly calling ORM methods or raw SQL without a repository interface; domain objects are being returned from API handlers without a mapping layer (ORM entity == API DTO is a persistence leak); transaction participation across multiple repository calls needs to be made explicit; or storage errors are propagating as raw ORM exceptions to callers.

# Do Not Use When

Do not use this capability to: design the underlying database schema (use `relational-database` or `nosql-database`); design the application service orchestration logic (use `service-business-logic`); design the API DTO contract (use `dto-schema-design`); or optimize a slow database query (use `indexing-query-optimization` — the repository interface is already defined, the query implementation needs tuning).

# Stage Fit

Owns backend persistence-boundary design during implementation planning, coding, code-review, refactoring, debugging, testing, release-readiness, and final handoff when the primary decision is how application/domain code talks to durable storage without leaking ORM/session/query mechanics. In planning, it turns current repository call sites, domain aggregate boundaries, storage models, and tests into a contract for methods, mapping, transaction participation, and error translation. In debugging or repair, separate mapper defects, repository method semantics, transaction scope, tenant/permission filters, query plans, and service orchestration before widening the boundary. In review and refactoring, reject ORM entity leakage, query-builder escape hatches, ambiguous not-found semantics, hidden lazy loading, unbounded queries, and transaction behavior that is not visible to the service layer. In testing and release-readiness, require fresh integration or validator evidence after the final repository, mapper, transaction, tenant-filter, or error-translation edit. Repository graph, project memory, and execution trajectory can identify prior persistence conventions or fragile files, but current source, tests, schema/mappers, and validation output must confirm the boundary before reuse.

# Non-Negotiable Rules

- **Repository interfaces must be defined in domain or application language, not storage language.** Method names on a repository interface should read like domain operations: `findByEmail(email)`, `findActiveOrdersForCustomer(customerId)`, `save(order)`, `remove(orderId)`. They must not read like database operations: `executeQuery(sql)`, `findByWhereClause(clause)`, `findAllWithJoin()`. Storage mechanics belong behind the interface implementation, not in the interface contract.
- **ORM-specific objects, query builders, and lazy-loading proxies must not cross the repository boundary.** Returning a Hibernate `PersistentBag`, a SQLAlchemy `InstrumentedList`, a Prisma `Delegate`, or a TypeORM `EntityManager` from a repository method means the caller can trigger additional database queries without the repository's knowledge. This is the "lazy-loading leakage" problem: a controller calls `user.orders` on an ORM entity, triggering an N+1 query that the repository never intended. Rule: repositories return domain objects or plain DTOs, never ORM entities. Map inside the repository.
- **Not-found, permission-filtered, and soft-deleted records must be handled explicitly, not conflated.** A `findById(id)` method has three meaningfully different outcomes: (1) record found and returned; (2) record does not exist (`null` / `Option.None` / `Result.Err(NotFound)`); (3) record exists but is soft-deleted or filtered by access control (`null` / `Option.None` / `Result.Err(NotFound)` — same result, different cause). Repository methods must document which of these are possible and what they return. Callers must not need to probe the difference by adding a `findByIdIncludingDeleted()` call to determine whether a record existed.
- **Transaction participation must be explicit in the repository contract.** Does this repository method participate in the current ambient transaction (Unit of Work pattern)? Does it create its own transaction? Does it require a transaction to be provided by the caller? The default behavior must be documented. A repository that silently starts a new transaction on every call will break transactional invariants when the caller expects the save to participate in an outer transaction. Explicit transaction scope (passed as parameter, or via Unit of Work / session scoping) is required for any repository used in multi-step write operations.
- **Storage errors must be translated to domain-meaningful outcomes before leaving the repository.** A `UniqueConstraintViolationException` from PostgreSQL is a storage detail. The caller should receive `DuplicateEmailAddressError` or `ConflictError`, not a raw ORM exception with a stack trace referencing database internals. The repository is the translation boundary. Rule: catch all storage-layer exceptions; map to domain or application exceptions; document what the caller can expect.
- **Query methods must declare their consistency, pagination, and ordering contract.** A `findAll()` method that returns up to 10,000 records is a production risk waiting to materialize. Repository query contracts must state: maximum result size (or require a pagination parameter); default ordering (or require explicit ordering); consistency level (read from primary? read replica?); and behavior when the result set is larger than expected (throw, truncate, paginate automatically).
- **Closure evidence must name the repository validator or integration-test command, validator/tool, artifact or report path, output and exit code or manual review result, changed repository/method/mapper scope, and freshness after the final repository-related edit.** Mock-only service tests, stale integration runs, or graph memory are not persistence-boundary proof.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| New repository contract | New aggregate/entity persistence point, new repository interface, or new data-access port. | Place interface at domain/application boundary, hide storage mechanics, and map domain language to durable storage. | Owning module, aggregate boundary, current naming convention, persistence model, mapper owner, and rejected locations. | `data-model-design`, `implementation-structure-design` | Infrastructure-first interface placement. |
| Existing method change | New query, changed not-found behavior, pagination, ordering, consistency, or soft-delete treatment. | Preserve callers while making method semantics explicit and testable. | Current callers, method contract, returned type, soft-delete/permission behavior, max result size, and old/new behavior risk. | `service-business-logic`, `indexing-query-optimization` when slow query risk exists | Generic `findAll` or query-builder leakage. |
| Transaction and unit-of-work boundary | Repository write participates in service transaction, batch write, lock, retry, or ambient session. | Make transaction participation visible to the caller and avoid hidden commits or remote calls inside locks. | Service transaction owner, write methods, lock/isolation expectation, Unit of Work/session scope, and rollback behavior. | `transaction-consistency`, `relational-database` | Repository-started hidden transactions. |
| Mapping and error translation | ORM entity, row/document, generated model, storage exception, or lazy proxy crosses boundary. | Map persistence records to domain/DTO intentionally and translate storage failures to domain/application outcomes. | Mapper source, field/null/default semantics, exception map, lazy-loading absence, and sensitive-field exclusion. | `model-boundary-mapping`, `failure-contract-design`, `security-privacy-gate` when sensitive | Returning raw ORM entities or raw exceptions. |
| Persistence integration proof | Repository contract is implemented or reviewed for constraints, queries, rollback, tenant filters, or OSIV absence. | Prove the real persistence boundary, not mocked repository behavior. | Real or equivalent DB test, fixture owner, tenant/soft-delete assertions, rollback/constraint test, and validation command. | `integration-testing`, `quality-test-gate` | Mock-only repository proof. |

# Industry Benchmarks

Anchor against Fowler's Repository and Data Mapper patterns, Evans DDD aggregate repositories, Clean Architecture dependency inversion, Unit of Work, ORM session/lazy-loading best practices, OSIV avoidance, and Testcontainers-style persistence integration testing. Keep this body focused on selection and evidence rules; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for method-contract matrices, implementation pattern examples, and detailed anti-pattern review.

# Selection Rules

Select this capability when **persistence boundary design is the primary concern** — the interface contract, mapping discipline, transaction participation, and error translation. Route elsewhere when: `relational-database` is primary (the table schema, constraints, migration plan — before the repository interface is defined); `transaction-consistency` is primary (designing isolation levels and locking strategy for complex concurrent write scenarios); `service-business-logic` is primary (the orchestration logic of the application service that calls the repository); `indexing-query-optimization` is primary (the query inside the repository implementation is slow and needs EXPLAIN ANALYZE tuning).

# Risk Escalation Rules

Escalate when: a repository method touches financial balances, inventory counts, or any invariant that can be violated by concurrent writes (requires explicit transaction and locking strategy from `transaction-consistency`); a repository serves multiple tenants and row-level filtering is required (requires tenant isolation verification — every query must have a tenant predicate); a soft-delete pattern is used and the filtering convention is not uniformly enforced (requires audit of all repository methods for `deleted_at IS NULL` filter coverage); bulk repository operations (`saveAll`, `deleteAll`) affect > 10k records (requires batching strategy and performance impact assessment); a repository is accessed from a background job without a scoped session or transaction boundary (requires session scope design for the job execution context).

# Proactive Professional Triggers

- **Signal:** Service, controller, or domain code imports ORM/session/query-builder types directly. **Hidden risk:** persistence mechanics leak into business flow and create unreviewed lazy queries or storage coupling. **Required professional action:** introduce or repair repository boundary and map inside implementation. **Route to:** `repository-persistence`, `implementation-structure-design`. **Evidence required:** import/caller scan, owner boundary, rejected direct-ORM access, and validation plan.
- **Signal:** Project memory, repository graph, or prior trajectory suggests a repository pattern to copy. **Hidden risk:** stale convention or fragile file gets reused without current-source confirmation. **Required professional action:** confirm current callers, tests, mappers, and conventions before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, freshness limit, accepted/rejected pattern, and evidence limits.
- **Signal:** A repository method returns `null`, empty list, `Option`, or exception without distinguishing not-found, soft-delete, permission filtering, and tenant filtering. **Hidden risk:** callers infer policy from absence and may leak existence, retry incorrectly, or create duplicate writes. **Required professional action:** document outcome taxonomy and translate it consistently. **Route to:** `failure-contract-design`, `security-privacy-gate` when access-controlled data is involved. **Evidence required:** method outcome table, caller expectation, and denied/filtered test obligation.
- **Signal:** A write method starts its own transaction, ignores ambient Unit of Work, or commits inside a service workflow. **Hidden risk:** partial commits and rollback mismatch across repositories. **Required professional action:** make transaction ownership explicit and hand off isolation/lock decisions. **Route to:** `transaction-consistency`, `service-business-logic`. **Evidence required:** service transaction owner, repository participation, rollback behavior, and concurrency risk.
- **Signal:** Repository proof relies on mocked repository tests while the risk is SQL, constraints, lazy loading, soft-delete, tenant predicate, or rollback. **Hidden risk:** tests validate fake behavior while production persistence fails. **Required professional action:** require real or equivalent DB integration coverage. **Route to:** `integration-testing`, `quality-test-gate`. **Evidence required:** test boundary, fixture isolation, DB/container, assertions, and residual untested path.
- **Signal:** Prior validation, project memory, or repository graph claims the persistence boundary is proven before a mapper, transaction policy, tenant filter, method return type, or error translation changes. **Hidden risk:** stale evidence hides a new boundary leak or untested persistence path. **Required professional action:** rerun or downgrade the repository proof and record validation freshness. **Route to:** `validation-broker`, `plan-execution-consistency`. **Evidence required:** command/report path, validator name, exit code, changed path, and what the stale evidence no longer proves.

# Critical Details

- **Aggregate roots only.** DDD repositories provide access to Aggregate roots only, not to child entities. If `Order` is an aggregate root and `OrderLineItem` is a child entity, there is no `OrderLineItemRepository`. Line items are accessed via `OrderRepository.findById(orderId)` and mutated through the `Order` aggregate. This enforces the aggregate consistency boundary: all changes to `Order` and its children happen within one transaction via one repository.
- **Read models do not need repositories.** In CQRS or read-optimized paths, a "read model" (a denormalized projection for a query page) does not need a domain repository interface. A simple `OrderSummaryQuery` class that executes a SQL query and returns a DTO is acceptable — it is not pretending to be a domain repository. The repository pattern is for aggregate persistence; read models are for query optimization.
- **Integration tests must use a real database, not a mocked repository.** Mocking a repository in an integration test proves nothing about the actual persistence behavior. Constraint enforcement, transaction rollback, lazy-loading behavior, and soft-delete filtering must all be tested against a real (or in-memory equivalent: SQLite, H2, Testcontainers) database. Unit tests mock repositories; integration tests do not.
- **The "Open Session In View" anti-pattern must be disabled.** Many web frameworks (Spring MVC, Django) enable a pattern where the database session/connection remains open through the view rendering phase, allowing lazy-loaded relationships to be fetched during serialization. This causes N+1 queries during HTTP response serialization, makes query behavior dependent on serialization order, and complicates transaction boundary reasoning. Disable OSIV; load all required data explicitly in the service/repository layer.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 repository-boundary selection and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete repository contract, when mapper/transaction/not-found coverage is uncertain, or before implementation starts. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when method contract classification, implementation examples, ORM leakage patterns, or anti-pattern details are needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load these references for pure routing or trivial wording work where the output contract and quality gate are enough.

# Failure Modes

- **ORM entity leak:** Domain service receives ORM entity; calls `user.orders` in a loop during HTTP request, triggering N+1 queries that work in dev with 10 users but cause 10-second latency in production.
- **Query-builder escape:** Repository returns `SelectQueryBuilder`; five callers build five different queries, one omits the `deleted_at IS NULL` filter, and soft-deleted data leaks into a customer-facing report.
- **Unbounded result contract:** `findAll()` without pagination runs in a scheduled report, returns 2M rows, causes an OOM crash, and leaves the report service unavailable.
- **Raw storage exception leak:** `UniqueConstraintViolationException` propagates to the API handler, returns a generic 500, and prevents clients from distinguishing "email taken" from "server broken".
- **Hidden transaction commit:** Repository `save()` starts its own transaction; the outer service transaction rolls back, but the repository commit already persisted partial state.
- **Infrastructure-owned interface:** Repository interface lives in `infrastructure/`; domain tests import infrastructure, dependency direction reverses, and the build develops circular dependencies.
- **Tenant predicate drift:** One repository method omits tenant or object-permission filtering while sibling methods include it, making absence semantics and existence-leak behavior inconsistent.
- **Stale integration proof:** Validation predates mapper, transaction, tenant-filter, or error-translation edits, so the handoff over-claims persistence proof that no longer matches the executed code path.

# Output Contract

Return a repository contract with:

- `mode_selected` (new contract, existing method change, transaction boundary, mapping/error translation, or integration proof)
- `boundary_scope` (owning module, aggregate/root, caller boundary, and rejected direct persistence access)
- `source_evidence` (current files, callers, mappers, tests, schema/config, repository graph, memory, or trajectory evidence inspected, with freshness limits)
- `interface_owner` (domain or application layer; package / module location)
- `methods` (per method: name, parameters with types, return type, not-found behavior, transaction participation)
- `domain_mapping` (mapper class/function; domain object ↔ persistence record conversion; field mapping rules)
- `query_semantics` (pagination requirement; max result size; ordering default; consistency level)
- `not_found_behavior` (per method: null / Option / exception; soft-delete vs non-existent distinction)
- `transaction_expectations` (ambient / new / caller-provided; Unit of Work participation; batch commit behavior)
- `session_and_lazy_loading_policy` (OSIV/session scope, eager/load plan, and lazy proxy escape prevention)
- `tenant_and_permission_filtering` (tenant predicate, object-level permission filter, and existence-leak behavior when relevant)
- `locking_notes` (pessimistic / optimistic; SELECT FOR UPDATE usage; conflict resolution)
- `error_translation` (storage exceptions → domain/application exceptions mapping)
- `performance_risks` (identified N+1 risks; query result size risks; missing index warnings)
- `integration_tests` (per method: test fixture; assertion; database used for test — must be real or equivalent)
- `changed_repository_to_validation_map` (each changed method/mapper/transaction/error path mapped to validator, integration test, or residual risk)
- `validation_commands` (repository or integration validator command, validator/tool, artifact/report path, relevant output, exit code or manual result, changed repository/method/mapper scope, and freshness verdict)
- `handoff_boundaries` (what is handed to service, schema, transaction, query tuning, security, or test gates)
- `evidence_limits` (what was not verified: real DB behavior, concurrency, production data volume, security filters, or query plans)

# Evidence Contract

Close a repository-persistence change only when the output names selected mode, boundary scope, current source evidence inspected, boundaries inspected, memory/graph/trajectory freshness when used, interface owner, mapper owner, method semantics, not-found/filtered behavior, transaction/session policy, error translation, integration-test or not-verified evidence, changed-repository-to-validation map, validation evidence, evidence limits, residual risk, and next handoff owner. A generic repository interface or "use repository pattern" statement is not sufficient evidence.

State what evidence proves, what evidence does not prove, reuse and placement rationale for repository graph, project memory, and execution trajectory claims, behavior preservation for existing callers/contracts, and the next gate before handoff. Validation evidence must include command names, validator/tool, artifact/report path, relevant output, exit code or manual review result, changed repository/method/mapper scope, and freshness after the final material edit; stale, mock-only, or graph-only proof must be downgraded to residual risk.

# Benchmark Coverage

Behavior improvement should be validated structurally: weak repository plans usually expose ORM entities, define interfaces in infrastructure, conflate absent/filtered records, hide transaction ownership, leave `findAll` unbounded, or prove persistence with mocks only. Improved outputs must name mode, boundary scope, source evidence, method semantics, mapper/error/session policy, validation mapping, and handoff boundaries while keeping detailed benchmark examples in references.

# Routing Coverage

Route here when the primary work is repository interface placement, domain/persistence mapping, query method semantics, transaction participation at the repository boundary, storage error translation, or ORM leakage review. Guard against over-routing by handing off when the primary concern is service orchestration (`service-business-logic`), conceptual schema/invariants (`data-model-design`), relational DDL/constraints (`relational-database`), query tuning (`indexing-query-optimization`), isolation/locking design (`transaction-consistency`), API DTO shape (`dto-schema-design`), or real-seam test planning (`integration-testing` / `quality-test-gate`).

# Quality Gate

The repository design is complete only when:

1. Interface is defined in domain or application layer — not infrastructure.
2. No ORM-specific types cross the repository boundary (interface or return types).
3. Not-found and soft-deleted cases are handled explicitly and documented.
4. Transaction participation is explicit for all write methods.
5. Storage exceptions are translated to domain-meaningful exceptions.
6. All query methods specify pagination, ordering, and consistency level.
7. Aggregate-root discipline is maintained — no child-entity repositories.
8. Integration tests use a real (or equivalent) database — not mocks.
9. OSIV is disabled; lazy-loading behavior outside repository is verified absent.
10. Multi-tenant repositories have tenant predicate coverage verified across all methods.
11. Selected mode, boundary scope, source evidence, and rejected locations are explicit.
12. Repository graph, project memory, and execution trajectory evidence are source-confirmed or marked not verified.
13. Each changed method, mapper, transaction policy, or error translation maps to a validator, integration test, or named residual risk.
14. Validation commands, validators, artifacts/reports, output and exit code or manual result, changed repository/method/mapper scope, and freshness are recorded for every accepted method, mapper, transaction, tenant-filter, error-translation, and integration-proof claim.
15. Handoff boundaries and evidence limits are named so repository evidence is not over-claimed as schema, query-plan, service, or production concurrency proof.

# Used By

- backend-change-builder
- data-middleware-change-builder

# Handoff

Hand off to `service-business-logic` for application orchestration and authorization-before-read ordering; `data-model-design` for conceptual schema and aggregate boundaries; `relational-database` for constraints, SQL DDL, and migration-sensitive relational design; `transaction-consistency` for isolation level, locking, and rollback semantics; `indexing-query-optimization` for query performance tuning; `integration-testing` for real database seam coverage; `security-privacy-gate` for tenant/object permission filtering or sensitive-data exposure; and `dto-schema-design` when API-visible shape must be separated from persistence internals.

# Completion Criteria

The capability is complete when **repository contracts preserve aggregate boundaries, return domain objects (never ORM entities), handle all not-found and error cases explicitly, and prove persistence behavior through integration tests against a real database**.
