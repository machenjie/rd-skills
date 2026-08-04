# Repository Persistence Benchmarks And Patterns

Load this reference when repository contract, persistence mapping, transaction participation, query bounds, tenancy/filtering, or real-store proof changes. Repository is a port around aggregate/data access, not a generic query bucket.

## Repository Contract Matrix

| Surface | Contract decision | Failure/proof |
| --- | --- | --- |
| Single lookup | Distinguish absent, filtered, deleted, wrong-tenant, or permission-hidden only when callers need that distinction. | No existence leak; uniqueness/query predicate and caller behavior are tested. |
| Collection/query | Bounded result, stable order/pagination, exactness/staleness and primary/replica source are explicit. | Reject unbounded `findAll`, hidden N+1/lazy loads, or unspecified count cost. |
| Save/batch | Return/result and per-item/partial-failure semantics are named. | Mapper round trip, constraints, transaction, rollback, and batch/load behavior. |
| Remove | Choose idempotent success vs typed absence plus soft/hard-delete, audit, tenant, retention and cascade behavior. | Retry/replay does not delete the wrong state or hide failure. |
| Exists/count | State whether filtered/approximate/stale results are acceptable. | Protected-resource existence and expensive scans do not leak or overload. |

## Boundary And Transaction Rules

- Define the interface in the owning domain/application boundary when dependency inversion is real; infrastructure owns ORM/SQL/session/client details.
- Keep ORM entities, lazy proxies, sessions, query builders, raw rows, and storage exceptions behind the selected public boundary. If a storage abstraction is intentionally public, name its accepted lifecycle, query, and compatibility effects.
- When persistence and domain/query shapes differ, an owned mapper or assembler preserves identity, null/default/enum/status semantics and sensitive-field exclusion; document any intentional shared type.
- Name Unit of Work and transaction ownership from the current architecture. Writes whose accepted use case requires joint rollback participate through its explicit or repository-standard convention and do not hide independent commits.
- Tenant/permission/soft-delete predicates and consistency source are enforced in the query boundary where relevant; read projections are named as queries/projections rather than aggregate repositories.

## Evidence And Routing

| Risk | Required proof | Limit |
| --- | --- | --- |
| Mapping/constraint | Real or equivalent store round trip, not-found/filter, unique/FK/check and typed error translation. | Mocks do not prove ORM, SQL, serialization, or constraint behavior. |
| Transaction | Commit/rollback across affected repositories, conflict/deadlock/error path, and outbox participation when present. | One happy save does not prove atomicity or retry safety. |
| Query | Generated SQL/query plan or representative log, bounds/order/pagination, tenant/delete filters, and expected cardinality. | Local tiny data does not prove production cost or replica freshness. |
| Freshness | Current interfaces, implementations, mappers, callers, migrations, tests and same-pattern repositories inspected after final edit. | Graph proximity and prior tests do not prove hidden/dynamic callers. |

Route domain ownership to `domain-logic-implementation`, model translation to `model-boundary-mapping`, query/index depth to `indexing-query-optimization`, atomicity to `transaction-consistency`, and API-visible absence/errors to `data-api-contract-changer`.

Reject repositories that return ORM/query builders, infrastructure-owned domain ports without rationale, unbounded lists, hidden transactions, raw storage failures, business rules in SQL/mapper code, mocked-only persistence proof, or tenant/delete filters left to callers.
