# Data Model Design Benchmarks And Patterns

Use this reference when `data-model-design` needs more than routing-level guidance. Keep the main `SKILL.md` focused on selection, evidence, and handoff rules; use this file for benchmark detail, storage choices, constraint patterns, and anti-pattern review.

## Benchmark Anchors

- **Domain-Driven Design:** entity, value object, aggregate, repository, domain event, aggregate boundary as transaction boundary, and ubiquitous language in model naming.
- **Designing Data-Intensive Applications:** document, relational, graph, storage, retrieval, replication, and consistency tradeoffs.
- **CQRS and event sourcing:** read model ownership, projection rebuild, event stream as source of truth, upcasting, and replay limits.
- **3NF and BCNF:** relational consistency baseline before deliberate denormalization.
- **Temporal modeling:** valid time, transaction time, SCD Type 2, append-only history, and audit reconstruction.
- **Regulated data standards:** GDPR erasure, CCPA deletion, HIPAA de-identification, PCI storage minimization, and financial ledger auditability.
- **OWASP secure data handling:** avoid dynamic SQL assembly, minimize public internal identifiers, and protect sensitive fields.
- **Database constraint practice:** `CHECK`, `UNIQUE`, `EXCLUDE`, `FOREIGN KEY`, deferrable constraints, partial indexes, and JSON Schema validation.

## Storage Type Selection Matrix

| Storage type | Invariant enforcement | Query flexibility | Schema evolution | Pick when |
| --- | --- | --- | --- | --- |
| Relational | Strong constraints and transactions. | High joins and aggregations. | DDL migration discipline required. | Structured data, relationships, ACID, reporting, or ad hoc query needs. |
| Document | Mostly application-level unless schema validation is enforced. | Access-pattern dependent. | Easy to add shape, hard to repair drift. | Hierarchical data with bounded embedded children and single aggregate ownership. |
| Time-series | Append-oriented, usually limited cross-row constraints. | Strong time-range access. | Additive evolution is easiest. | Metrics, events, sensor data, observability, or immutable measurements. |
| Graph | Relationship traversal is first-class; constraints vary by engine. | Strong path and pattern traversal. | Labels and edge types evolve. | Complex many-to-many relationship traversal is the main product behavior. |
| Key-value | Minimal structural enforcement. | Key lookup only. | Caller-owned serialization. | Session state, counters, caches, feature snapshots, or simple lookup. |
| Wide-column | Partition/clustering-key driven. | Query shape fixed by key design. | Column-family evolution, with operational cost. | High-write distributed data where query paths are known upfront. |
| Event store | Append-only ordering and stream identity. | Requires projections for reads. | New events and upcasters. | Event-sourced aggregates, audit reconstruction, replay, and temporal truth. |

## Normalization And Read Model Decisions

Start normalized when relational consistency matters. Denormalize only when a named query, latency target, volume profile, or ownership boundary proves the need.

Decision checks:

- If denormalized data is authoritative, reject the design unless there is a single writer and reconciliation protocol.
- If denormalized data is derived, require source-of-truth owner, staleness tolerance, rebuild path, and consumer behavior during rebuild.
- If a query joins more than three large tables on every hot path, compare query optimization, pre-joined read model, and domain model split before copying data.
- If a 1:few relationship is always read and written with the parent and shares the same owner, embedding or JSON may be acceptable with explicit constraints.
- If a 1:many or many-to-many relationship has independent lifecycle, ownership, or query paths, use a separate entity/table/document.
- If a many-to-many relationship carries status, metadata, ordering, audit, or lifecycle, model it as an explicit junction entity rather than an implicit join table.

## Invariant Enforcement Patterns

Use the database or storage engine as the last line of defense when feasible; application-only enforcement fails under direct SQL, scripts, bulk imports, jobs, or partial deploys.

Common patterns:

- **Required lifecycle field:** `NOT NULL` only after backfill or creation path guarantees the value.
- **Finite state:** constrained enum, lookup table, or check constraint plus service-layer transition checks.
- **Conditional attribute:** check constraint linking timestamp/field presence to lifecycle state.
- **Soft-delete uniqueness:** partial unique index for active rows only.
- **Temporal fact:** insert new row and close previous validity window instead of overwriting auditable history.
- **Cross-row invariant:** unique/exclusion constraint where supported; otherwise document transaction isolation and service-level lock strategy.
- **External identifier:** unique per provider/source, stored separately from internal primary key.

Example state constraints:

```sql
CREATE TYPE order_status AS ENUM ('draft', 'submitted', 'confirmed', 'shipped', 'delivered', 'cancelled');

ALTER TABLE orders
  ADD CONSTRAINT order_status_not_null CHECK (status IS NOT NULL),
  ADD CONSTRAINT shipped_at_valid CHECK (shipped_at IS NULL OR status IN ('shipped', 'delivered')),
  ADD CONSTRAINT cancelled_at_valid CHECK (cancelled_at IS NULL OR status = 'cancelled');
```

## Ownership Boundary Map

| Boundary question | Rule |
| --- | --- |
| Who creates this record? | Only the owning service creates identity, creation timestamp, and required initial state. |
| Who updates each attribute? | Single writer per attribute; other services request change through API/command/event protocol. |
| Who deletes or anonymizes? | Named owner plus authorization gate, audit rule, retention policy, and downstream notification. |
| How do other services read it? | API, event, projection, or replicated read model; avoid direct shared-database reads. |
| What if legacy shared DB exists? | Define write authority per table and column; make non-owners read-only until ownership is isolated. |
| How are external IDs mapped? | Separate integration-owned cross-reference table with provider/source scope and uniqueness. |
| What does project memory prove? | Nothing alone; confirm memory against current files, schemas, migrations, generated artifacts, and tests. |

## Relationship And Cardinality Patterns

- Model cardinality with real business limits, not UI convenience. "Usually one" is not the same as `1:1`.
- Prefer foreign keys where referential integrity matters and the storage engine supports them.
- Avoid polymorphic association columns like `target_type` plus `target_id` when referential integrity is required; use explicit junction tables.
- Add ownership and lifecycle to junction entities when relationships can be created, removed, approved, rejected, ordered, or audited.
- For recursive relationships, require cycle rules, maximum depth, traversal query plan, and deletion semantics.
- For graph-like models in relational storage, state why graph traversal needs do not justify a graph database or projection.

## Temporal, Retention, And Deletion Patterns

- Use effective dating when business validity matters: `valid_from`, `valid_to`, and non-overlap constraints where possible.
- Use transaction time when audit reconstruction matters: immutable event or history table with append timestamp.
- Use SCD Type 2 when attributes must be queried "as of" a date without losing prior values.
- Treat soft-delete as a product requirement, not a default. Require query filters, uniqueness behavior, retention, recovery, and erasure impact.
- Separate anonymization from deletion when legal deletion conflicts with financial, audit, or operational history.
- For regulated data, classify fields and define retention, minimization, access control, audit, export, and erasure behavior before schema acceptance.

## Evidence Patterns

A strong data-model-design handoff includes:

- current source paths inspected and how freshness was established;
- entity and attribute ownership with single-writer evidence;
- invariants mapped to database constraints, service validation, or accepted residual risk;
- query/write patterns with expected volume and concurrency;
- old/new model diff for existing data;
- compatibility impact for old readers, old writers, generated clients, reports, and jobs;
- migration path or explicit handoff to `data-migration-design`;
- DTO/API separation map or explicit handoff to contract capabilities;
- validation commands or review artifacts and what they prove;
- evidence limits and next gate.

## Anti-Patterns To Reject

| Anti-pattern | Why it fails |
| --- | --- |
| Table or document mirrors a UI form. | UI flow becomes source of truth and domain invariants disappear. |
| `json_data` stores most fields in a relational table. | Constraints, query planning, migration, ownership, and auditing become ad hoc. |
| Nullable field has no lifecycle meaning. | Invalid and ambiguous states become representable. |
| `status` is an unconstrained string. | Typos and unsupported states silently enter the source of truth. |
| Polymorphic `target_type` and `target_id` for critical relationships. | No real foreign key, weak joins, and orphaned records. |
| Direct service-to-service database reads. | Schema changes become hidden API breaks and ownership becomes unclear. |
| Read projection becomes authoritative. | Staleness, rebuilds, and reconciliation are unowned. |
| Soft-delete without partial indexes and deletion policy. | Unique constraints, query filters, erasure, and retention become inconsistent. |
| Migration feasibility deferred until release. | Conceptual design may require unsafe DDL, unbounded backfill, or dual-write retrofits. |
| Prior project memory accepted without source confirmation. | Stale agent trajectory can override current code, migrations, registry, or generated artifacts. |
