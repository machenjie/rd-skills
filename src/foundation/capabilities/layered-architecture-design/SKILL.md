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

# Non-Negotiable Rules

- **Controllers (Presentation) must not contain business decisions.** A controller may: parse transport input (deserialize, validate format via DTO), call an application service method, and format the response. It must not: branch on business conditions (`if order.status == 'processing'`), calculate values, or enforce business policies. The litmus test: if the same use case is triggered by a CLI command, a queue consumer, or a scheduled job — the business behavior must work unchanged without the HTTP layer.
- **Domain must not depend on Infrastructure.** No import of database clients, ORM sessions, HTTP clients, queue producers, file system APIs, or framework containers inside a domain entity, value object, or domain service. The domain defines repository interfaces (ports); Infrastructure implements them (adapters). This is the Dependency Inversion Principle applied to layers.
- **Application service orchestrates; it does not own business invariants.** Application services coordinate: "load the Order, call `order.confirm()`, save via repository, publish the OrderConfirmed event." The invariant "an order cannot be confirmed if payment is pending" lives in the Order domain object — not in the application service. An application service that contains `if order.paymentStatus != 'completed': raise ValidationError` is leaking domain logic.
- **Infrastructure exceptions must not leak into domain or application layers as framework types.** `psycopg2.errors.UniqueViolation`, `SqlException`, `MongoWriteConcernError` must be caught at the repository adapter boundary and re-thrown as domain exceptions (`DuplicateOrderException`, `PersistenceException`). Domain and application code must never import or catch database-specific exception classes.
- **Transactions belong to the Application layer.** The unit of work (transaction boundary) spans use cases, not individual repository calls. A domain entity must not start or commit transactions. A repository must not open a cross-entity transaction. The application service (or a unit-of-work pattern) manages the transaction scope.
- **Dependency direction is enforced by tooling, not convention.** Architecture conventions without automated enforcement erode over time. Use: **ArchUnit** (Java) — `layeredArchitecture().layer("Domain").definedBy("..domain..")...noDependency()...`; **Dependency Cruiser** (JavaScript/TypeScript) — `.dependency-cruiser.js` with forbidden import rules; **import-linter** (Python) — `[importlinter:contract:domain-no-infra]`; **NDepend** (.NET) — dependency matrix rules. These checks must run in CI.

# Industry Benchmarks

Anchor against: **Robert C. Martin "Clean Architecture"** (2017) — Entities (domain), Use Cases (application), Interface Adapters (presentation/infrastructure), Frameworks/Drivers; dependency rule: inner layers know nothing about outer layers; the most cited architectural text for layer discipline. **Alistair Cockburn "Hexagonal Architecture / Ports and Adapters"** (2005, alistair.cockburn.us) — application core (domain + application services) surrounded by ports (interfaces) and adapters (implementations); enables testing the core without adapters. **Eric Evans "Domain-Driven Design"** (2003, Addison-Wesley) — Layered Architecture (Ch. 4): UI, Application, Domain, Infrastructure; "Domain layer is the heart of the business software." **Martin Fowler "Patterns of Enterprise Application Architecture"** (2002) — Service Layer, Repository, Domain Model, Table Module, Transaction Script patterns; placement rules for business logic. **Onion Architecture** (Jeffrey Palermo, 2008) — concentric rings; domain core at center; application services; infrastructure at periphery; dependency inward only. **SOLID — Dependency Inversion Principle** (Robert Martin) — high-level modules must not depend on low-level modules; both must depend on abstractions. **Spring (Java) layer conventions** — `@Controller` → `@Service` → `@Repository`; stereotype annotations enforce layer awareness (not enforced by language; requires ArchUnit for rule enforcement). **NestJS (TypeScript)** — Modules, Controllers, Services, Repositories; `@Injectable()` + DI container; facilitates Hexagonal but does not enforce it. **pytest / JUnit test architecture** — domain unit tests: no mocks needed (pure functions / value objects); application service tests: mock repository interfaces; infrastructure tests: real DB via Testcontainers.

### Layer Responsibility Table

| Layer | Owns | Must not contain | Depends on | Typical types |
| --- | --- | --- | --- | --- |
| Presentation | Transport parsing, request validation, response formatting, auth header extraction | Business rules, database queries, domain decisions | Application | Controller, Handler, Resolver, Presenter, DTO (request/response) |
| Application | Use case orchestration, transaction boundary, authorization invocation, event publishing coordination | Business invariants, persistence details, HTTP/transport details | Domain (via interfaces); Infrastructure (via DI injection of interfaces) | ApplicationService, UseCase, CommandHandler, QueryHandler, UnitOfWork |
| Domain | Business invariants, entity lifecycle, value objects, domain events, domain services, business calculations | Database clients, HTTP clients, framework imports, environment config | Nothing (pure) | Entity, ValueObject, AggregateRoot, DomainService, Repository (interface), DomainEvent |
| Infrastructure | Persistence (ORM, SQL), external API HTTP clients, message producers/consumers, file I/O, framework adapters | Business rules, domain decisions | Domain (implements domain interfaces); Application (implements application ports) | Repository (impl), DbModel, HttpAdapter, MessageProducer, CacheAdapter |

### Dependency Direction Enforcement

```
Correct dependency direction:
  Presentation → Application → Domain ← Infrastructure

                +------------------+
                |   Presentation   |  (Controllers, DTOs)
                +--------↓---------+
                |   Application    |  (Use Cases, Services)
                +--------↓---------+
                |     Domain       |  (Entities, Value Objects, Interfaces)
                +------- ↑ --------+
                | Infrastructure   |  (Repositories, HTTP Adapters)
                +------------------+

Domain defines:
  interface OrderRepository {
    findById(id: OrderId): Order | null
    save(order: Order): void
  }

Infrastructure implements:
  class PostgresOrderRepository implements OrderRepository {
    constructor(private db: Database) {}
    findById(id: OrderId): Order | null {
      const row = this.db.query('SELECT * FROM orders WHERE id = $1', [id.value])
      return row ? Order.reconstitute(row) : null
    }
  }
  // ← Infrastructure imports domain interface and entity
  // ← Domain does NOT import PostgresOrderRepository

ArchUnit enforcement (Java):
  layeredArchitecture()
    .layer("Presentation").definedBy("..presentation..")
    .layer("Application").definedBy("..application..")
    .layer("Domain").definedBy("..domain..")
    .layer("Infrastructure").definedBy("..infrastructure..")
    .whereLayer("Domain").mayNotAccessLayersExcept()
    .whereLayer("Application").mayNotAccessLayersExcept("Domain")
    .whereLayer("Presentation").mayNotAccessLayersExcept("Application")
```

### Business Logic Placement Decision Tree

```
Is this a CALCULATION, POLICY, or INVARIANT?
  → Domain layer (Entity method, Domain Service, Value Object)

Is this a WORKFLOW STEP that coordinates multiple domain objects,
transactions, authorization, or events?
  → Application Service / Use Case

Is this about PARSING REQUEST / VALIDATING FORMAT / FORMATTING RESPONSE?
  → Presentation layer (Controller, DTO validator)

Is this about READING/WRITING to external storage or calling external APIs?
  → Infrastructure layer (Repository impl, HTTP adapter)

Anti-test:
  "Can I unit-test this without starting a DB, HTTP server, or framework container?"
    YES → Domain logic is correct
    NO  → Domain logic has leaked into Infrastructure or Application has Infrastructure imports
```

# Selection Rules

Select this capability when **business logic placement and dependency direction** are the primary concern. Adjacent routing:

- Prefer `module-boundary-design` when the primary concern is bounded context boundaries and which modules can import which other modules.
- Prefer `service-business-logic` when implementing the application service details is primary (not the layer assignment question).
- Prefer `domain-logic-implementation` when implementing domain entities, value objects, and invariants is primary.
- Prefer `microservice-splitting` when the question is whether a bounded context should be extracted into a separate deployable service.
- Prefer `architecture-tradeoff-analysis` when the decision is between layered, CQRS, event-sourcing, or other macro-architecture patterns.

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

# Failure Modes

- Controller contains `if subscription.plan == 'enterprise' and feature_flag: return enhanced_response` — business rule duplicated across 3 controllers; plan change requires updating all 3; inconsistency bug.
- Domain entity imports SQLAlchemy model to resolve a lazy relationship — ORM session required to unit-test domain logic; test startup time triples.
- Application service catches `psycopg2.errors.ForeignKeyViolation` directly — domain and application code now coupled to PostgreSQL; migration to a different database requires changes in application layer.
- Repository interface in application layer — domain entities cannot reference the repository type without importing application package; domain tests require application imports.
- Domain event raised inside domain with a Kafka producer injected — domain tests require a Kafka broker; 20-second startup penalty per test run.
- Transaction managed inside individual repository methods — two repository calls in an application service run in two separate transactions; partial commit on failure creates inconsistent data.

# Output Contract

Return a layer responsibility map with:

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

# Quality Gate

The layer design is complete only when:

1. Controller contains no business conditional logic; delegates entirely to application service.
2. Domain entities and services have zero imports from infrastructure or framework packages.
3. Repository interfaces defined in domain layer; implementations in infrastructure.
4. Infrastructure exceptions mapped to domain exceptions at the adapter boundary.
5. Transaction boundary defined in application layer (not in repository or domain).
6. Domain logic is unit-testable without starting a database, HTTP server, or framework container.
7. Dependency direction rule implemented in automated tool (ArchUnit, dependency-cruiser, import-linter) and runs in CI.
8. Business invariants live in domain entities/services, not in application service conditional checks.
9. Domain events raised inside domain boundary; published by application service after use case completes.
10. Transaction Script vs Domain Model decision documented for each aggregate (justified choice, not assumed).

# Used By

- architecture-impact-reviewer
- backend-change-builder

# Handoff

Hand off to `module-boundary-design` for cross-module import rules; `service-business-logic` for application service implementation details; `domain-logic-implementation` for entity and value object design; `transaction-consistency` for distributed transaction patterns.

# Completion Criteria

The capability is complete when **layer responsibilities are explicit, dependency direction is machine-enforced in CI, business invariants live in the domain, controllers contain no business decisions, and domain logic is unit-testable without any infrastructure dependency**.
