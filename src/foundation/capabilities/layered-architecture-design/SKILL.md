---
name: layered-architecture-design
description: Defines presentation, application, domain, and infrastructure responsibilities with dependency direction and business logic placement rules.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "20"
changeforge_version: 0.1.0
---

# Mission

Keep business behavior in the right layer by defining **presentation, application, domain, and infrastructure responsibilities with enforceable dependency direction** — ensuring domain logic is testable without infrastructure, controllers contain no business decisions, and every layer depends only inward: never domain → infrastructure, never presentation → persistence.

# When To Use

Use this capability when a change: introduces a new use case that crosses multiple layers; adds a controller, handler, or route that must delegate to service logic; places business rules in a service or domain object and needs layer assignment; adds a repository, external API adapter, or database query that must be isolated from domain logic; or is flagged in review for "business logic in the controller" or "domain calls the database directly."

# Do Not Use When

Do not use this capability to force unnecessary layering ceremony on a small, isolated change that already follows established layering and has no business-rule risk. Do not use it to impose a canonical folder structure on a team that has established a different — but internally consistent — architecture; consistency within a codebase outweighs theoretical correctness of an external standard.

# Stage Fit

Use during architecture-design, implementation-planning, coding, code-review, refactoring, debugging, testing, and release-readiness when presentation, application, domain, infrastructure, repository, adapter, transaction, exception, or dependency-direction responsibility is unclear. In planning, define layer ownership, dependency rules, exceptions, test seams, and enforcement before implementation. In coding/review, reject stale project-memory or repository-graph claims unless current imports, package layout, service/repository/domain code, tests, and architecture checks confirm the layering behavior. Hand off when the primary question is module ownership, architecture style choice, concrete service orchestration, domain invariant implementation, persistence design, or distributed transaction behavior.

# Non-Negotiable Rules

- **Controllers (Presentation) must not contain business decisions.** A controller may: parse transport input (deserialize, validate format via DTO), call an application service method, and format the response. It must not: branch on business conditions (`if order.status == 'processing'`), calculate values, or enforce business policies. The litmus test: if the same use case is triggered by a CLI command, a queue consumer, or a scheduled job — the business behavior must work unchanged without the HTTP layer.
- **Domain must not depend on Infrastructure.** No import of database clients, ORM sessions, HTTP clients, queue producers, file system APIs, or framework containers inside a domain entity, value object, or domain service. The domain defines repository interfaces (ports); Infrastructure implements them (adapters). This is the Dependency Inversion Principle applied to layers.
- **Application service orchestrates; it does not own business invariants.** Application services coordinate: "load the Order, call `order.confirm()`, save via repository, publish the OrderConfirmed event." The invariant "an order cannot be confirmed if payment is pending" lives in the Order domain object — not in the application service. An application service that contains `if order.paymentStatus != 'completed': raise ValidationError` is leaking domain logic.
- **Infrastructure exceptions must not leak into domain or application layers as framework types.** `psycopg2.errors.UniqueViolation`, `SqlException`, `MongoWriteConcernError` must be caught at the repository adapter boundary and re-thrown as domain exceptions (`DuplicateOrderException`, `PersistenceException`). Domain and application code must never import or catch database-specific exception classes.
- **Transactions belong to the Application layer.** The unit of work (transaction boundary) spans use cases, not individual repository calls. A domain entity must not start or commit transactions. A repository must not open a cross-entity transaction. The application service (or a unit-of-work pattern) manages the transaction scope.
- **Dependency direction is enforced by tooling, not convention.** Architecture conventions without automated enforcement erode over time. Use: **ArchUnit** (Java) — `layeredArchitecture().layer("Domain").definedBy("..domain..")...noDependency()...`; **Dependency Cruiser** (JavaScript/TypeScript) — `.dependency-cruiser.js` with forbidden import rules; **import-linter** (Python) — `[importlinter:contract:domain-no-infra]`; **NDepend** (.NET) — dependency matrix rules. These checks must run in CI.
- **Closure evidence names the architecture check command, validator/tool, artifact/report path, exit code or manual result, import graph scope, changed paths, and freshness after the final layer-related edit.** A stale successful architecture check from before import or package movement is not completion evidence.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Layer responsibility map | New controller/service/domain/repository/adapter or unclear use-case placement. | Assign presentation, application, domain, and infrastructure responsibilities. | Current package layout, entry point, use case, domain objects, repository/adapters, rejected placements. | `implementation-structure-design`, `module-boundary-design` | Macro architecture style debate. |
| Dependency direction enforcement | Import cycle, domain imports ORM/framework, application imports HTTP/DB client, or no architecture check. | Inward dependency rule and machine enforcement. | Import graph, forbidden import list, existing or proposed ArchUnit/dependency-cruiser/import-linter rule. | `architecture-enforcement-tooling`, `quality-test-gate` | Manual convention-only review. |
| Business rule placement | Business condition in controller/service/repository, duplicated invariant, or anemic domain concern. | Put invariants in domain or justify transaction script. | Rule name, actor/use case, domain owner, current duplicate sites, test seam. | `domain-logic-implementation`, `service-business-logic` | Rich domain model for trivial CRUD. |
| Transaction and exception boundary | Transaction scope, infrastructure exception, unit of work, or adapter error mapping is unclear. | Application transaction ownership and adapter exception translation. | Participating repositories, rollback rule, exception map, unit-of-work owner. | `transaction-consistency`, `repository-persistence` | Distributed saga design unless needed. |
| Framework and adapter isolation | Framework decorators, ORM models, HTTP clients, queues, files, or env access appear in core code. | Keep core testable without framework/infrastructure startup. | Import scan, adapter boundary, constructor/port seam, test command. | `test-strategy`, `repository-persistence` | Framework tutorial detail. |
| Architecture exception review | Team uses transaction script, Active Record, framework-first layering, or deliberate shortcut. | Name exception, owner, expiry/review trigger, and tests that contain risk. | Local convention, simpler alternative, risk accepted, enforcement or residual risk. | `architecture-impact-reviewer`, `minimal-correct-implementation` | Dogmatic clean-architecture rewrite. |

# Industry Benchmarks

Anchor against Clean Architecture, Hexagonal/Ports and Adapters, DDD Layered Architecture, Fowler's Service Layer/Repository/Domain Model/Transaction Script patterns, Onion Architecture, SOLID Dependency Inversion, framework layer conventions, architecture fitness functions, and test pyramids that keep domain tests infrastructure-free. Keep this body focused on routing, layer decisions, evidence, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for layer responsibility matrices, dependency enforcement examples, business logic placement rules, graph/memory/trajectory coupling, and anti-pattern review.

# Selection Rules

Select this capability when **business logic placement and dependency direction** are the primary concern. Adjacent routing:

- Prefer `module-boundary-design` when the primary concern is bounded context boundaries and which modules can import which other modules.
- Prefer `service-business-logic` when implementing the application service details is primary (not the layer assignment question).
- Prefer `domain-logic-implementation` when implementing domain entities, value objects, and invariants is primary.
- Prefer `microservice-splitting` when the question is whether a bounded context should be extracted into a separate deployable service.
- Prefer `architecture-tradeoff-analysis` when the decision is between layered, CQRS, event-sourcing, or other macro-architecture patterns.

# Proactive Professional Triggers

- **Signal:** a controller, resolver, route, CLI handler, or queue consumer contains business conditionals, calculations, or policy checks. **Hidden risk:** delivery mechanisms diverge and duplicate rules. **Required professional action:** move behavior to application/domain boundary and define the layer map. **Route to:** `service-business-logic`, `domain-logic-implementation`. **Evidence required:** current entry point, rule name, target layer, and test seam.
- **Signal:** domain objects, value objects, or domain services import ORM models, database sessions, HTTP clients, queues, filesystem APIs, framework containers, or environment config. **Hidden risk:** domain behavior cannot be tested or reused without infrastructure. **Required professional action:** introduce/confirm ports and adapter implementations. **Route to:** `repository-persistence`, `implementation-structure-design`. **Evidence required:** import scan, port/interface owner, adapter owner, domain-only test.
- **Signal:** architecture is said to be layered because folders exist, but no dependency rule runs in CI. **Hidden risk:** convention decays silently. **Required professional action:** define architecture fitness check or name residual risk. **Route to:** `architecture-enforcement-tooling`, `quality-test-gate`. **Evidence required:** ArchUnit/dependency-cruiser/import-linter/NDepend rule or not-verified enforcement limit.
- **Signal:** project memory, repository graph, or prior trajectory claims a layering pattern already exists. **Hidden risk:** stale layer labels hide current imports, framework coupling, or exception leaks. **Required professional action:** confirm current source imports, package layout, tests, and validation freshness before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected pattern, freshness limit.
- **Signal:** a team proposes Clean/Hexagonal/Onion layering for simple CRUD or a tiny isolated change. **Hidden risk:** ceremony and pass-through layers reduce efficiency without protecting behavior. **Required professional action:** decide transaction script versus domain model explicitly. **Route to:** `minimal-correct-implementation`, `architecture-impact-reviewer`. **Evidence required:** business-rule count, invariant complexity, rejected heavier layer, and test boundary.

# Risk Escalation Rules

Escalate when: a controller contains branching business policies that would change if the delivery mechanism changed; a domain entity imports an ORM model or database client; an application service imports `psycopg2`, `Hibernate`, `axios`, or equivalent infrastructure library directly; a change removes a repository interface (domain contract) and replaces it with a direct ORM query in the application service; or the team cannot unit-test domain logic without starting a database container.

# Critical Details

- **"Thin controller" is necessary but not sufficient.** Controllers that delegate entirely to application services are a necessary condition for correct layering. But if the application service contains the business invariant (`if order.status != 'confirmed': raise InvalidStateError`), the invariant has moved one layer inward but still not into the domain. The business invariant belongs in `Order.confirm()` which raises `InvalidStateError` if the order is in a state that forbids confirmation.
- **Repository interface in domain, not in application.** Some teams put the repository interface in the application layer. The repository interface is a domain concept — it is the domain's description of how it expects to persist and retrieve its own entities. Domain services and application services call the repository. The interface belongs in the domain; the implementation belongs in infrastructure.
- **Domain events vs application events.** A `DomainEvent` (`OrderConfirmed`) is raised inside the domain when an invariant transition occurs — inside `order.confirm()`. The application service is responsible for *collecting* those events and publishing them to the event bus (domain does not publish events directly, as that would couple domain to infrastructure). This is the correct separation.
- **Transaction Script vs Domain Model.** For simple CRUD operations with no significant business invariants, a Transaction Script (direct application service → repository without rich domain objects) is appropriate and simpler. Do not force Domain Model pattern onto CRUD. Domain Model is justified when there are multiple business rules, state machines, and invariants. Over-engineering simple CRUD with rich domains adds cost without benefit.

### Anti-examples

| Anti-pattern | Layer violation | Fix |
| --- | --- | --- |
| `if order.isPaid and user.isActive: grant_access()` in controller | Business decision in Presentation | Move to Application Service or Domain |
| `from sqlalchemy.orm import Session` imported in Order entity | Infrastructure import in Domain | Order entity must not know about ORM; use Repository interface |
| Application service opens DB transaction and calls repository.save() in a loop | Application layer micro-manages persistence | Use UnitOfWork; let Repository batch or the transaction scope handle atomicity |
| `except psycopg2.errors.UniqueViolation` in Application Service | Infrastructure exception in Application | Repository adapter catches and re-raises as `DuplicateOrderException` |
| All application services have 10+ constructor dependencies | God class; orchestrating too much | Split into multiple focused use cases; extract domain services |
| Domain Service calls `requests.get('https://...')` | Infrastructure call in Domain | Define a port interface in domain; implement HTTP adapter in infrastructure |

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 layer selection, stage fit, evidence, output, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete layer map, dependency direction rule, business logic placement, transaction boundary, exception mapping, or architecture enforcement obligation. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when detailed benchmark anchors, responsibility matrices, enforcement snippets, placement decision trees, graph/memory/trajectory coupling, or anti-pattern review is needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or minor wording edits where the inline output contract and quality gate are enough.

# Failure Modes

- **Stale graph closure**: project memory says "domain has no infrastructure imports," but the import graph was not rerun after a new adapter or package move; a hidden domain -> ORM edge reaches release.
- **Unowned layer exception**: a temporary framework-first shortcut has no owner, expiry, containment test, or residual risk; later refactoring normalizes the exception across new features.
- Controller contains `if subscription.plan == 'enterprise' and feature_flag: return enhanced_response` — business rule duplicated across 3 controllers; plan change requires updating all 3; inconsistency bug.
- Domain entity imports SQLAlchemy model to resolve a lazy relationship — ORM session required to unit-test domain logic; test startup time triples.
- Application service catches `psycopg2.errors.ForeignKeyViolation` directly — domain and application code now coupled to PostgreSQL; migration to a different database requires changes in application layer.
- Repository interface in application layer — domain entities cannot reference the repository type without importing application package; domain tests require application imports.
- Domain event raised inside domain with a Kafka producer injected — domain tests require a Kafka broker; 20-second startup penalty per test run.
- Transaction managed inside individual repository methods — two repository calls in an application service run in two separate transactions; partial commit on failure creates inconsistent data.

# Output Contract

Return a layer responsibility map with:

- `mode_selected` (layer responsibility map / dependency direction enforcement / business rule placement / transaction and exception boundary / framework and adapter isolation / architecture exception review)
- `layering_scope` (use case, module/package boundary, included layers, excluded modules, local architecture convention)
- `source_evidence` (current controllers/handlers, application services, domain objects, repositories/adapters, imports, tests, architecture checks, repository graph, project memory, and execution trajectory inspected with freshness limits)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for each reused layer convention, import rule, repository pattern, transaction pattern, exception mapping, test pattern, or architecture check)
- `entry_points` (controllers, handlers, consumers; what they parse and delegate)
- `application_use_cases` (named use cases; transaction boundaries; authorization invocation; event publishing coordination)
- `domain_rules` (entities; value objects; domain services; invariants; which rules live where)
- `repository_interfaces` (defined in: domain; implemented in: infrastructure; method signatures)
- `infrastructure_adapters` (repository implementations; HTTP clients; message producers; exception mapping)
- `dependency_direction` (diagram or table: what imports what; direction of each dependency)
- `transaction_boundary` (which use case(s) open transactions; which repositories participate; rollback on exception)
- `validation_boundary` (format/schema validation: Presentation; business/ownership validation: Application + Domain)
- `exception_mapping` (infrastructure exception → domain exception: table of mappings)
- `test_strategy` (domain: pure unit test; application: unit with repository mock; infrastructure: integration with Testcontainers)
- `enforcement` (ArchUnit / dependency-cruiser / import-linter rule: run in CI)
- `validation_commands` (architecture/import check command, validator/tool, artifact/report path, exit code or manual result, changed path scope, and freshness verdict)
- `layer_exception_decisions` (transaction script, Active Record, framework-first, or legacy exception with reason, owner, expiry/review trigger, and containment test)
- `changed_layer_to_validation_map` (each entry point, use case, domain rule, repository interface, adapter, transaction boundary, exception mapping, dependency rule, architecture exception, and enforcement check mapped to validator/test or residual risk)
- `handoff_boundaries` (what belongs to module boundary, service orchestration, domain invariant, repository/persistence, transaction consistency, architecture style, or quality/test gate)
- `evidence_limits` (what was not inspected or run: full import graph, actual CI architecture rule, target project tests, DB/infrastructure tests, framework startup, generated clients, or production package layout)

# Evidence Contract

Close a layered-architecture output only when it names selected mode, layer scope, current source evidence, graph/memory/trajectory reuse judgment, boundaries inspected, entry points, application use cases, domain rules, repository interfaces, infrastructure adapters, dependency direction, transaction boundary, validation boundary, exception mapping, test strategy, enforcement rule or residual risk, layer exceptions, changed-layer-to-validation map, handoff boundaries, residual risk, and evidence limits. A folder list, "use clean architecture", or "controllers call services" statement is not sufficient evidence.

Validation evidence must name command, validator, artifact/report path, exit code or manual result, changed path scope, and freshness after the final material import/layer/edit. State what evidence proves, what evidence does not prove, reuse and placement rationale for graph/memory/trajectory claims, behavior preservation for existing layer conventions and exceptions, and next gate/handoff owner.

# Benchmark Coverage

Improved layer outputs reject common weak patterns: controller business conditionals, domain imports of ORM/framework/HTTP code, application services catching infrastructure exceptions, repositories owning cross-aggregate transactions, domain events publishing directly to Kafka, pass-through services with no boundary reason, rich domain models for trivial CRUD, architecture rules that exist only as convention, and stale project-memory claims about layering. Detailed benchmark anchors, responsibility tables, enforcement examples, and placement decision trees belong in references so the body stays efficient.

# Routing Coverage

Route here when presentation/application/domain/infrastructure responsibilities, dependency direction, business logic placement, repository interface ownership, transaction scope, infrastructure exception mapping, or architecture enforcement is primary. Hand off when the primary concern is module ownership/public API (`module-boundary-design`), macro architecture style (`architecture-style-selection`), concrete application service orchestration (`service-business-logic`), domain invariant implementation (`domain-logic-implementation`), persistence adapter design (`repository-persistence`), distributed transaction/idempotency (`transaction-consistency` / `idempotency-retry-design`), or executable architecture checks (`quality-test-gate` / `architecture-enforcement-tooling`).

# Quality Gate

The layer design is complete only when:

1. Selected mode, layer scope, source evidence, and graph/memory/trajectory reuse judgment are explicit.
2. Controller contains no business conditional logic; delegates entirely to application service.
3. Domain entities and services have zero imports from infrastructure or framework packages.
4. Repository interfaces are defined in the domain or explicitly justified local convention; implementations live in infrastructure/adapters.
5. Infrastructure exceptions are mapped to domain/application exceptions at the adapter boundary.
6. Transaction boundary is defined in application layer or unit-of-work owner, not hidden in repository/domain code.
7. Domain logic is unit-testable without starting a database, HTTP server, framework container, queue, or external API.
8. Dependency direction rule is implemented in an automated tool and runs in CI, or the missing enforcement is named as residual risk.
9. Business invariants live in domain entities/services, not duplicated in controller/application conditional checks.
10. Domain events are raised inside domain boundary and published by application service/outbox after the use case reaches a consistent state.
11. Transaction Script vs Domain Model decision is documented for each aggregate/use case, with complexity justification.
12. Every deliberate layer exception has owner, reason, expiry/review trigger, and containment test or residual risk.
13. Each changed entry point, use case, domain rule, repository interface, adapter, transaction boundary, exception mapping, dependency rule, and enforcement check maps to validation evidence or named residual risk.
14. Validation commands, validators, artifacts/reports, exit code or manual result, changed path scope, and freshness are recorded for every accepted import, layer exception, or enforcement claim.
15. Handoff boundaries and evidence limits are explicit so layer evidence is not over-claimed as module boundary, domain implementation, persistence, distributed transaction, or CI enforcement proof.

# Used By

- architecture-impact-reviewer
- backend-change-builder

# Handoff

Hand off to `module-boundary-design` for cross-module import rules; `service-business-logic` for application service implementation details; `domain-logic-implementation` for entity and value object design; `transaction-consistency` for distributed transaction patterns.

# Completion Criteria

The capability is complete when **layer responsibilities are explicit, dependency direction is machine-enforced in CI, business invariants live in the domain, controllers contain no business decisions, and domain logic is unit-testable without any infrastructure dependency**.
