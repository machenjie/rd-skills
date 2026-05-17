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

# Non-Negotiable Rules

- **Repository interfaces must be defined in domain or application language, not storage language.** Method names on a repository interface should read like domain operations: `findByEmail(email)`, `findActiveOrdersForCustomer(customerId)`, `save(order)`, `remove(orderId)`. They must not read like database operations: `executeQuery(sql)`, `findByWhereClause(clause)`, `findAllWithJoin()`. Storage mechanics belong behind the interface implementation, not in the interface contract.
- **ORM-specific objects, query builders, and lazy-loading proxies must not cross the repository boundary.** Returning a Hibernate `PersistentBag`, a SQLAlchemy `InstrumentedList`, a Prisma `Delegate`, or a TypeORM `EntityManager` from a repository method means the caller can trigger additional database queries without the repository's knowledge. This is the "lazy-loading leakage" problem: a controller calls `user.orders` on an ORM entity, triggering an N+1 query that the repository never intended. Rule: repositories return domain objects or plain DTOs, never ORM entities. Map inside the repository.
- **Not-found, permission-filtered, and soft-deleted records must be handled explicitly, not conflated.** A `findById(id)` method has three meaningfully different outcomes: (1) record found and returned; (2) record does not exist (`null` / `Option.None` / `Result.Err(NotFound)`); (3) record exists but is soft-deleted or filtered by access control (`null` / `Option.None` / `Result.Err(NotFound)` — same result, different cause). Repository methods must document which of these are possible and what they return. Callers must not need to probe the difference by adding a `findByIdIncludingDeleted()` call to determine whether a record existed.
- **Transaction participation must be explicit in the repository contract.** Does this repository method participate in the current ambient transaction (Unit of Work pattern)? Does it create its own transaction? Does it require a transaction to be provided by the caller? The default behavior must be documented. A repository that silently starts a new transaction on every call will break transactional invariants when the caller expects the save to participate in an outer transaction. Explicit transaction scope (passed as parameter, or via Unit of Work / session scoping) is required for any repository used in multi-step write operations.
- **Storage errors must be translated to domain-meaningful outcomes before leaving the repository.** A `UniqueConstraintViolationException` from PostgreSQL is a storage detail. The caller should receive `DuplicateEmailAddressError` or `ConflictError`, not a raw ORM exception with a stack trace referencing database internals. The repository is the translation boundary. Rule: catch all storage-layer exceptions; map to domain or application exceptions; document what the caller can expect.
- **Query methods must declare their consistency, pagination, and ordering contract.** A `findAll()` method that returns up to 10,000 records is a production risk waiting to materialize. Repository query contracts must state: maximum result size (or require a pagination parameter); default ordering (or require explicit ordering); consistency level (read from primary? read replica?); and behavior when the result set is larger than expected (throw, truncate, paginate automatically).

# Industry Benchmarks

Anchor against: **Martin Fowler "Patterns of Enterprise Application Architecture" (PoEAA, 2002)** — Repository pattern (p. 322): "mediates between the domain and data mapping layers using a collection-like interface"; Data Mapper pattern (p. 165): maps between in-memory objects and persistent store without coupling the objects to the store. **Domain-Driven Design (Evans, 2003)** — Repository provides access to Aggregate roots only; never provides access to child entities directly; enforces aggregate boundary. **Robert Martin "Clean Architecture" (2017)** — dependency inversion: domain layer defines the repository interface; infrastructure layer implements it; never the reverse. **Spring Data JPA / Hibernate best practices** — `@Transactional` boundary placement; avoiding LazyInitializationException; Open Session In View anti-pattern (disables lazy-loading fix by extending session scope into the view layer — widely considered an anti-pattern). **TypeORM / Prisma / SQLAlchemy documentation** — ORM-specific object lifecycle management; detached entity behavior; session scope. **Unit of Work pattern** — transactional boundary that coordinates multiple repository operations; commit or rollback as an atomic unit. **Integration testing with Testcontainers** — proving persistence behavior against a real database instance, not mocked repositories.

### Repository Method Contract Classification

| Method Type | Returns | Not-Found Behavior | Transaction Participation | Consistency |
| --- | --- | --- | --- | --- |
| `findById(id)` | `Option<DomainObject>` or throws `NotFoundError` | None / Option.None / NotFoundError | Read-only; participates in ambient or starts new read | Primary or replica — must be stated |
| `findBy*(criteria)` single | `Option<DomainObject>` | None / Option.None | Read-only | Primary or replica |
| `findAll*(criteria)` list | `List<DomainObject>` with pagination | Empty list (not null) | Read-only | Primary or replica |
| `save(domainObject)` | `DomainObject` (with generated ID) | N/A | Requires ambient transaction or creates one | Primary write |
| `saveAll(list)` | `List<DomainObject>` | N/A | Requires transaction; documents batch behavior | Primary write |
| `remove(id)` | `void` or `boolean` | Idempotent OR throws `NotFoundError` — must be stated | Requires ambient transaction | Primary write |
| `exists(criteria)` | `boolean` | false | Read-only | May be replica |
| `count(criteria)` | `long` | 0 | Read-only | May be replica (approximate) |

### Repository Implementation Pattern

```typescript
// Interface: defined in domain/application layer — no ORM types
interface OrderRepository {
  findById(id: OrderId): Promise<Order | null>;
  findActiveByCustomerId(
    customerId: CustomerId,
    pagination: Pagination
  ): Promise<PagedResult<Order>>;
  save(order: Order): Promise<Order>;
  remove(id: OrderId): Promise<void>;
}

// Implementation: defined in infrastructure layer
class PostgresOrderRepository implements OrderRepository {
  constructor(private readonly db: DatabaseConnection) {}

  async findById(id: OrderId): Promise<Order | null> {
    const row = await this.db.query(
      'SELECT * FROM orders WHERE id = $1 AND deleted_at IS NULL',
      [id.value]
    );
    if (!row) return null;  // explicit null — not undefined, not empty array
    return OrderMapper.toDomain(row);  // maps DB record to domain object
  }

  async save(order: Order): Promise<Order> {
    try {
      const row = OrderMapper.toRecord(order);  // domain → DB record
      const saved = await this.db.upsert('orders', row);
      return OrderMapper.toDomain(saved);
    } catch (error) {
      if (isUniqueConstraintViolation(error)) {
        throw new DuplicateOrderIdError(order.id);  // translate, don't re-throw raw
      }
      throw new PersistenceError('Failed to save order', { cause: error });
    }
  }
}

// OrderMapper: bidirectional mapping
class OrderMapper {
  static toDomain(row: OrderRecord): Order { /* ... */ }
  static toRecord(order: Order): OrderRecord { /* ... */ }
}
```

### Repository Boundary Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `userService.getUser(id)` calls `user.orders` on returned ORM entity | LazyInitializationException in production; N+1 queries in dev; ORM session scope leaked to service | Repository returns domain `User` with `orders` as a loaded collection or via separate `OrderRepository.findByUserId()` |
| Repository returns `TypeORM SelectQueryBuilder` | Caller builds arbitrary queries; repository boundary is useless; query logic scattered across codebase | Repository exposes named methods with specific domain semantics; query builder stays inside implementation |
| `findAll()` with no pagination | Returns entire table; works in dev (100 rows); OOM or timeout in production (10M rows) | Require `Pagination` parameter; throw if `limit > MAX_LIMIT`; default ordering required |
| Raw ORM exception propagates to controller: `QueryFailedError: duplicate key value` | Exposes database internals to caller; caller must parse exception message to detect conflict | Catch `QueryFailedError`; re-throw `DuplicateEmailError` in the repository implementation |
| Repository interface defined in infrastructure layer | Domain layer depends on infrastructure; violates dependency inversion; cannot test domain without database | Define interface in `domain/` or `application/`; implement in `infrastructure/`; inject via DI |
| `save(user)` starts a new transaction, ignoring ambient transaction | Multi-step write: `userRepo.save()` + `auditRepo.save()` are in separate transactions; audit record saved even if user save rolls back | Participate in ambient Unit of Work; or require explicit transaction to be passed as parameter |

# Selection Rules

Select this capability when **persistence boundary design is the primary concern** — the interface contract, mapping discipline, transaction participation, and error translation. Route elsewhere when: `relational-database` is primary (the table schema, constraints, migration plan — before the repository interface is defined); `transaction-consistency` is primary (designing isolation levels and locking strategy for complex concurrent write scenarios); `service-business-logic` is primary (the orchestration logic of the application service that calls the repository); `indexing-query-optimization` is primary (the query inside the repository implementation is slow and needs EXPLAIN ANALYZE tuning).

# Risk Escalation Rules

Escalate when: a repository method touches financial balances, inventory counts, or any invariant that can be violated by concurrent writes (requires explicit transaction and locking strategy from `transaction-consistency`); a repository serves multiple tenants and row-level filtering is required (requires tenant isolation verification — every query must have a tenant predicate); a soft-delete pattern is used and the filtering convention is not uniformly enforced (requires audit of all repository methods for `deleted_at IS NULL` filter coverage); bulk repository operations (`saveAll`, `deleteAll`) affect > 10k records (requires batching strategy and performance impact assessment); a repository is accessed from a background job without a scoped session or transaction boundary (requires session scope design for the job execution context).

# Critical Details

- **Aggregate roots only.** DDD repositories provide access to Aggregate roots only, not to child entities. If `Order` is an aggregate root and `OrderLineItem` is a child entity, there is no `OrderLineItemRepository`. Line items are accessed via `OrderRepository.findById(orderId)` and mutated through the `Order` aggregate. This enforces the aggregate consistency boundary: all changes to `Order` and its children happen within one transaction via one repository.
- **Read models do not need repositories.** In CQRS or read-optimized paths, a "read model" (a denormalized projection for a query page) does not need a domain repository interface. A simple `OrderSummaryQuery` class that executes a SQL query and returns a DTO is acceptable — it is not pretending to be a domain repository. The repository pattern is for aggregate persistence; read models are for query optimization.
- **Integration tests must use a real database, not a mocked repository.** Mocking a repository in an integration test proves nothing about the actual persistence behavior. Constraint enforcement, transaction rollback, lazy-loading behavior, and soft-delete filtering must all be tested against a real (or in-memory equivalent: SQLite, H2, Testcontainers) database. Unit tests mock repositories; integration tests do not.
- **The "Open Session In View" anti-pattern must be disabled.** Many web frameworks (Spring MVC, Django) enable a pattern where the database session/connection remains open through the view rendering phase, allowing lazy-loaded relationships to be fetched during serialization. This causes N+1 queries during HTTP response serialization, makes query behavior dependent on serialization order, and complicates transaction boundary reasoning. Disable OSIV; load all required data explicitly in the service/repository layer.

# Failure Modes

- Domain service receives ORM entity; calls `user.orders` in a loop during HTTP request — N+1 queries; works in dev (10 users); 10-second latency in production (10,000 users).
- Repository returns `SelectQueryBuilder` — 5 different callers build 5 different queries — one omits the `deleted_at IS NULL` filter — soft-deleted data leaks into a customer-facing report.
- `findAll()` without pagination — scheduled report runs at midnight — 2M rows returned — OOM crash — report service unavailable for 20 minutes.
- Raw `UniqueConstraintViolationException` propagates to API handler — handler has no catch for it — unhandled exception returns 500 — client cannot distinguish "email taken" from "server broken".
- Repository `save()` starts its own transaction — outer service transaction rolls back — `save()` was already committed — partial state in database.
- Repository interface defined in `infrastructure/` package — domain tests must import infrastructure — circular dependency — build fails.

# Output Contract

Return a repository contract with:

- `interface_owner` (domain or application layer; package / module location)
- `methods` (per method: name, parameters with types, return type, not-found behavior, transaction participation)
- `domain_mapping` (mapper class/function; domain object ↔ persistence record conversion; field mapping rules)
- `query_semantics` (pagination requirement; max result size; ordering default; consistency level)
- `not_found_behavior` (per method: null / Option / exception; soft-delete vs non-existent distinction)
- `transaction_expectations` (ambient / new / caller-provided; Unit of Work participation; batch commit behavior)
- `locking_notes` (pessimistic / optimistic; SELECT FOR UPDATE usage; conflict resolution)
- `error_translation` (storage exceptions → domain/application exceptions mapping)
- `performance_risks` (identified N+1 risks; query result size risks; missing index warnings)
- `integration_tests` (per method: test fixture; assertion; database used for test — must be real or equivalent)

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

# Used By

- backend-change-builder
- data-middleware-change-builder

# Handoff

Hand off to `data-model-design` for schema design; `transaction-consistency` for isolation level and locking strategy; `indexing-query-optimization` for query performance tuning; `service-business-logic` for application service orchestration that calls the repository.

# Completion Criteria

The capability is complete when **repository contracts preserve aggregate boundaries, return domain objects (never ORM entities), handle all not-found and error cases explicitly, and prove persistence behavior through integration tests against a real database**.
