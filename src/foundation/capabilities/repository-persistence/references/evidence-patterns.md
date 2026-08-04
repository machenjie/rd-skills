# Repository Persistence Evidence Patterns

Use this reference when repository-persistence closure depends on validation freshness, prior source or task evidence claims, ORM/tenant/transaction proof, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second repository pattern catalog.

## Repository-To-Validation Map

| Repository claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Interface boundary is correctly placed | Owning module, interface path, rejected infrastructure/direct-ORM location, caller scan, and dependency direction review | Inspected repository boundary follows intended ownership | Future modules or hidden direct storage access are prevented |
| ORM/storage mechanics do not leak | Method signatures, returned types, mapper path, lazy/session policy, and import scan | Inspected callers do not receive obvious ORM/query-builder objects | Serialization, runtime lazy loads, or all generated types are impossible |
| Method semantics are explicit | Method list, parameters, return type, not-found/soft-delete/permission behavior, pagination/order/consistency rule | Inspected methods have clear caller contracts | All callers handle every outcome correctly |
| Transaction participation is visible | Write methods, service transaction owner, Unit of Work/session scope, rollback behavior, and concurrency handoff/test | Inspected writes have a transaction ownership model | Isolation anomalies or production contention are solved |
| Error translation is owned | Storage exception list, domain/application outcome map, sensitive-detail suppression, and failure test/review | Inspected storage errors do not obviously leak raw internals | Every storage provider error or localization path is handled |
| Tenant/permission filtering is consistent | Query methods, tenant/object predicate, existence-leak behavior, denied/filtered tests, and security owner | Inspected protected reads have a filter and absence policy | All report jobs, admin tools, or raw SQL paths are covered |
| Persistence proof is real enough | Real/equivalent DB integration test, fixture owner, constraint/rollback/lazy/tenant assertions, and freshness after final edit | Inspected repository behavior was tested outside pure mocks | Production volume, query plans, or cross-service concurrency are proven |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, old conventions, generated clients, schema docs, and prior tests as selectors until current callers, mappers, schema/config, and fresh validation confirm them.
- Accept prior "repository pattern is established", "OSIV disabled", "tenant filter always applied", or "integration tests cover it" claims only when current source and validation still match.
- Mark evidence stale after edits to repository interfaces, methods, mappers, transaction policy, tenant filters, error translation, schema, generated clients, tests, reports, or build outputs.
- Map each changed repository decision to a current command, test, report, owner review, or explicit not-run residual risk.
- Add a handoff when closure crosses an owner boundary.

- If production query, migration, data repair, transaction replay, or tenant-filter change, record environment, owner approval, stop condition, rollback or containment path, and redaction rule.
- If production telemetry, audit, or support query, keep access read-only or approved-connector-scoped, aggregate sensitive labels, and redact tenant/user/secret-bearing fields.
