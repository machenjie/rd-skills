# Relational Database Evidence Patterns

Use this reference when relational database closure depends on validation freshness, prior source or task evidence claims, schema/query/migration proof, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second relational design guide.

## Schema-To-Validation Map

| Relational claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Storage fit is justified | Invariant list, source-of-truth owner, access patterns, transaction need, and rejected NoSQL/cache/search alternatives | The inspected workload has a reason to use relational storage | Future volume, uninspected query plans, and live lock behavior remain unproven |
| Critical invariant is constrained | Table/column map, PK/FK/UNIQUE/CHECK/NOT NULL design, writer owner, and constraint/integration test or review | Inspected invariant has database-layer enforcement | Uninspected writers, migration scripts, and replica paths remain outside the claim |
| Transaction behavior is explicit | Rows/tables touched, isolation level, lock order, deadlock/retry behavior, and concurrency test or handoff | Inspected write path has an atomicity and conflict plan | Production contention and untested anomalies remain unproven |
| Index supports a real query | SQL/ORM caller, predicates, sort/join, cardinality estimate, existing/proposed indexes, and EXPLAIN or residual risk | Inspected index maps to a named query | Long-tail production plans or future query variants are safe |
| Migration is deployable | Row/write volume, lock class, selected rollout/backfill/cutover phases, validation query, recovery or rollback tier, and release owner | Inspected migration has a safe sequence and validation map | Actual production lock timing, replica lag, or rollback RTO is proven |
| Tenant/PII boundary is protected | Tenant/object filter, parameterized SQL, data classification, retention/encryption note, and denied/negative test or review | Inspected query/schema path addresses obvious disclosure risk | Security certification and approval of downstream report consumers remain separate decisions |
| API remains decoupled from schema | Mapper/DTO boundary, generated-client impact, forbidden ORM entity exposure, and compatibility test/review | Inspected schema detail is not directly exposed as API contract | Compatibility of uninspected external consumers and generated clients remains unproven |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, generated docs, migration ledgers, report jobs, telemetry, and prior validation as selectors until current schema, code, tests, and fresh execution confirm them.
- Recheck prior "no readers", "already indexed", "migration is safe", or "tenant filters are universal" claims against current source, migrations, reports, and validation.
- Mark evidence stale after edits to DDL, migrations, query callers, indexes, generated clients, repository methods, tenant filters, report consumers, tests, reports, or build outputs.
- Map each changed relational-data decision to current evidence or an explicit not-run residual risk.
- Add unverified-consumer or recovery risk when material.
- Add a handoff when closure crosses an owner boundary.

- If production DDL, live backfill, index build, destructive migration, or report consumer change, record environment, owner approval, stop condition, rollback or containment path, and redaction rule.
- If production query, telemetry, or warehouse/report inspection, keep access read-only or approved-connector-scoped, aggregate sensitive labels, and redact tenant/user/secret-bearing fields.
