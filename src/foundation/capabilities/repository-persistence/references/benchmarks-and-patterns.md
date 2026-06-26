# Repository Persistence Benchmarks And Patterns

Use this reference when a repository-persistence output needs more detail than the `SKILL.md` body can carry efficiently. Keep the main skill body focused on routing, evidence, and quality gates.

## Benchmark Anchors

- Fowler, Patterns of Enterprise Application Architecture: Repository mediates between domain and data mapping layers; Data Mapper keeps persistent store details outside domain objects.
- Domain-Driven Design: repositories expose aggregate roots and preserve aggregate boundaries.
- Clean Architecture: domain/application layer owns the repository interface; infrastructure implements it.
- Unit of Work: coordinates multiple repository operations under one transaction.
- ORM session/lazy-loading guidance: persistence session lifetime must not leak into services, controllers, or serializers.
- Testcontainers-style integration testing: repository persistence behavior is proved against a real or equivalent database, not mocks.

## Repository Method Contract Matrix

| Method type | Return contract | Not-found or filtered behavior | Transaction participation | Evidence required |
| --- | --- | --- | --- | --- |
| `findById(id)` | `Option<DomainObject>`, nullable domain object, or typed `NotFound` | Distinguish absent, soft-deleted, tenant-filtered, or permission-filtered where relevant | Read-only; ambient or explicit read session stated | Caller expectations, filter policy, and not-found tests. |
| `findBy(criteria)` single | Optional domain object or typed result | No multiple-match ambiguity | Read-only; consistency source stated | Uniqueness expectation and query predicate. |
| `listBy(criteria, page)` | Paged result; never unbounded list | Empty list for no matches | Read-only; replica/primary consistency stated | Limit, order, cursor/offset policy, max page size. |
| `save(aggregate)` | Saved aggregate or command result | N/A | Ambient Unit of Work or explicit transaction required | Mapper round trip, constraint/error translation, rollback behavior. |
| `saveAll(batch)` | Batch result with per-item semantics | N/A | Transaction/batch behavior stated | Batch size, partial failure policy, performance risk. |
| `remove(id)` | Idempotent success or typed `NotFound` | Must state idempotent-vs-error semantics | Write transaction required | Soft-delete/hard-delete rule and audit/tenant filter. |
| `exists(criteria)` | Boolean | False includes absent/filtered unless distinguished | Read-only | No existence leak for protected resources. |
| `count(criteria)` | Exact or approximate count | Zero for no matches | Read-only; replica/primary stated | Exactness, cost, stale-read tolerance. |

## Interface And Implementation Pattern

```typescript
// Interface: defined in domain/application layer, no ORM types.
interface OrderRepository {
  findById(id: OrderId): Promise<Order | null>;
  listActiveByCustomerId(
    customerId: CustomerId,
    page: PageRequest
  ): Promise<Page<Order>>;
  save(order: Order, tx?: UnitOfWork): Promise<Order>;
}

// Implementation: infrastructure layer owns SQL/ORM/session details.
class PostgresOrderRepository implements OrderRepository {
  constructor(private readonly db: DatabaseConnection) {}

  async findById(id: OrderId): Promise<Order | null> {
    const row = await this.db.oneOrNone(
      "SELECT * FROM orders WHERE id = $1 AND deleted_at IS NULL",
      [id.value]
    );
    return row ? OrderMapper.toDomain(row) : null;
  }

  async save(order: Order, tx?: UnitOfWork): Promise<Order> {
    try {
      const row = OrderMapper.toRecord(order);
      const saved = await (tx ?? this.db).upsert("orders", row);
      return OrderMapper.toDomain(saved);
    } catch (error) {
      if (isUniqueConstraintViolation(error)) {
        throw new DuplicateOrderIdError(order.id);
      }
      throw new PersistenceFailure("Failed to save order", { cause: error });
    }
  }
}
```

## Boundary Review Checklist

- Interface lives in domain/application layer; implementation lives in infrastructure.
- Public contract uses domain IDs/value objects or stable DTOs, not ORM entities.
- Mapper owns null/default/enum/status conversion and sensitive-field exclusion.
- No query builder, session, entity manager, lazy proxy, or raw row escapes.
- Each method names not-found/filtered behavior and max result size.
- Write methods name transaction participation and rollback behavior.
- Storage exceptions map to domain/application errors.
- Tenant, permission, and soft-delete filters are stated where relevant.
- Read models are called queries/projections, not aggregate repositories.
- Integration proof uses real or equivalent database for persistence risks.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| Repository returns ORM entity or lazy collection | Callers trigger hidden queries and session errors. | Return domain object/DTO with required data loaded. |
| Repository returns query builder | Query rules scatter across callers. | Expose named methods with explicit semantics. |
| Interface defined in infrastructure | Domain depends on storage implementation. | Define port in domain/application; implement in infrastructure. |
| `findAll()` without pagination | Dev works; production returns millions of rows. | Require page/cursor and stable order. |
| Raw storage exception leaves repository | Controllers parse DB errors or leak internals. | Translate to domain/application failure. |
| Repository starts hidden transaction | Service rollback does not cover all writes. | Participate in Unit of Work or explicit caller transaction. |
| Mocked repository proves persistence behavior | Constraints, rollback, SQL, and filters are untested. | Use real/equivalent DB integration test for persistence seam. |
