# Data Model Design Benchmarks And Patterns

Load this reference when storage fit, source-of-truth ownership, normalization/read models, invariant enforcement, cardinality, temporal history, retention, or deletion changes the model. Do not select a store or schema from generic popularity.

## Storage Fit

| Shape | Use when | Required caution/proof |
| --- | --- | --- |
| Relational | Relationships, transactions, constraints, joins, or reporting are central. | DDL/migration, query plan, concurrency, and constraint behavior. |
| Document | One aggregate owns a bounded nested shape and access follows it. | Schema drift, partial update, size, and child lifecycle remain controlled. |
| Time-series/wide-column | Append/high-write data has known time/partition access paths. | Partition/cardinality, retention, compaction, and late/out-of-order data. |
| Graph | Relationship traversal is primary product behavior. | Edge/identity constraints, traversal cost, deletion, and operational ownership. |
| Key-value/cache | Key lookup and caller-owned serialization match the authoritative contract. | It is not silently promoted from derived/cache state to source of truth. |
| Event store | Ordered streams and audit/replay are authoritative. | Event identity/version/upcasting, projection rebuild, privacy, and replay limits. |

## Model And Invariant Decisions

- Choose normalization or denormalization from current consistency, query, latency, volume, ownership, and history evidence. For duplicated state, name authoritative writer/source, staleness tolerance, reconciliation, rebuild, and consumer behavior during rebuild.
- Embed only when child data shares owner, lifecycle, write boundary, and access pattern. Separate an entity/relationship when identity, lifecycle, ownership, query path, metadata, ordering, approval, or audit is independent.
- Model real cardinality and failure states, not UI convenience. Critical relationships use enforceable references where supported; polymorphic references need an explicit integrity/orphan strategy.
- Recursive relationships name cycle policy, depth/traversal bounds or query plan, and deletion/cascade semantics from current domain behavior.
- External identifiers are unique within their provider/source scope and remain separate from internal identity; mapping ownership and collision behavior are explicit.
- Enforce critical invariants at the strongest current boundary: application feedback plus storage constraint where feasible. For cross-row rules, name uniqueness/exclusion/locking/isolation and the residual race.
- Required fields, lifecycle/state constraints, soft-delete uniqueness, external identifiers, and tenant ownership are introduced only after existing data and mixed-version writers can satisfy them.

## Ownership, History, And Deletion

| Concern | Required decision | Escalate when |
| --- | --- | --- |
| Identity/write authority | Name creator and mutation authority for each attribute; non-authoritative writers use an owned API, command, event, or projection. | Shared database or direct reads make schema an undeclared contract. |
| Derived/read model | Name authoritative source, update/rebuild path, lag tolerance, and reconciliation owner. | Projection becomes authoritative or cannot be rebuilt. |
| Temporal history | Choose effective time, transaction time, append history, or current-state-only from audit/as-of needs. | Overlap, correction, timezone, or replay semantics are unresolved. |
| Retention/soft delete | Define filters, uniqueness, recovery, retention, access, and erasure behavior; soft delete is not a default. | Legal deletion conflicts with ledger/audit/operational history. |
| Regulated/sensitive fields | Classify and minimize; name encryption/tokenization, access/audit, export, retention, anonymization, and deletion owner. | Policy or downstream copies are unknown. |

## Evidence And Routing

- Record current schemas/migrations, owners/writers, invariants and enforcement, query/write/concurrency profile, existing-data diff, old/new consumers, migration path, DTO/API separation, validation, and what remains unverified.
- Current source proves inspected readers/writers only; generated clients, reports, jobs, dynamic queries, replicas, and external consumers require separate evidence.
- Route entity/aggregate semantics to `domain-object-identification`, migrations to `data-migration-design`, contracts to `dto-schema-design`/`version-compatibility`, engine behavior to `relational-database`/`nosql-database`, and regulated data to `security-privacy-gate`.

Reject UI-form schemas as domain truth, unowned JSON blobs, unconstrained ambiguous lifecycle fields, and critical polymorphic references without integrity. Also reject service-to-service shared-table reads, authoritative projections without rebuild, soft delete without policy, and migration feasibility deferred to release.
