---
name: data-model-design
description: Designs data models from invariants, query patterns, ownership, lifecycle, migration risk, concurrency behavior, regulatory requirements, and separation between persistence internals and external contracts.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "25"
changeforge_version: 0.1.0
---

# Mission

Design data models that **encode domain invariants as close to the source of truth as possible, support required query and write patterns without future emergency rewrites, enforce ownership and lifecycle boundaries, minimize migration risk through deliberate evolution planning, and cleanly separate persistence internals from API contracts** — so that the system remains correct under concurrent writes, query demands, team autonomy, and regulatory requirements.

# When To Use

Use this capability when a change: introduces a new entity, aggregate, or document; adds, removes, or renames attributes or columns; changes relationships or cardinality (1:1, 1:N, M:N); adds or modifies uniqueness constraints, foreign key constraints, or check constraints; normalizes or denormalizes a model; introduces or modifies a read model (materialized view, projection, CQRS read side); changes ownership boundaries (who owns and writes this data); defines lifecycle states or status progressions; specifies data retention, archival, or deletion policies; or designs a schema that will be directly exposed to other services.

# Do Not Use When

Do not use this capability to mirror a UI form directly into a database table — forms reflect UX concerns; models reflect domain invariants. Do not use it to expose persistence tables as API contracts — use `dto-schema-design` and `api-contract-design`. Do not use it for query performance optimization on an existing schema — that is physical tuning; use `relational-database` or `nosql-database`. Do not use it to design migration scripts for existing data — use `data-migration-design`.

# Stage Fit

Use during planning, coding, bug-fix, debugging, code-review, refactoring, testing, release, and handoff when persisted data shape, source-of-truth ownership, invariant enforcement, model boundary mapping, or a remembered model claim can affect correctness, compatibility, migration safety, privacy, or downstream query behavior.

Use during planning when source-of-truth data shape, entity ownership, relationship cardinality, invariants, lifecycle states, retention, query/write pattern fit, or storage-family choice is unresolved. Use during implementation review when a patch changes persisted fields, constraints, aggregate boundaries, derived read models, or persistence/API separation. Use during testing when invariants, null/default semantics, referential integrity, retention/deletion behavior, or model-boundary mapping need validation evidence. Hand off before release to `data-migration-design` for live stored-data change sequencing, to `dto-schema-design`/`api-contract-design` for client-visible shapes, and to `repository-persistence` for application persistence boundary placement. Skip for pure DTO wording, physical index tuning, or migration runbook execution when the conceptual model is already accepted.

# Non-Negotiable Rules

- **Model invariants first, storage second.** Define what must always be true (invariants), what constitutes an invalid state, what transitions are allowed, and who owns each attribute — before choosing table structure, document structure, or index layout. Storage is a physical concern; invariants are a domain concern.
- **Every entity has a single owner.** No attribute is written by two services without a defined authority and sync protocol. Shared mutable state with no ownership is the root cause of data inconsistency at scale. Ownership is per-attribute, not just per-table.
- **Invalid states must be unrepresentable where feasible.** Use database constraints (NOT NULL, UNIQUE, CHECK, FOREIGN KEY), enumeration columns with allowlisted values, state machine enforcement (CHECK constraint on status with allowed transitions), and nullable semantics deliberately. A `status` column that can simultaneously have `started_at` populated and `status = 'pending'` is an invalid state that is fully representable — design it out.
- **Nullable fields encode lifecycle intent, not laziness.** A nullable column means "this attribute does not always exist for this entity." If it is nullable only because the value is not known at creation but becomes required later, that is a lifecycle state — model it as a state transition (status column), separate table, or temporal attribute with `created_at` / `filled_at` markers.
- **Query and write patterns drive physical design, not the reverse.** Before choosing normalization level, partition key, index strategy, or document embedding, list: the 3-5 most critical query patterns (read access patterns), the write rate and write pattern (append-only, update-heavy, time-series), the cardinality of each relationship, and the expected data volume. These determine whether normalization, denormalization, embedded documents, or materialized views are appropriate.
- **Migration risk is evaluated at design time.** Before finalizing a model, assess: can a column be added safely (nullable first)? can it be renamed without a dual-write phase? can it be dropped without affecting other services? Models designed without migration awareness become unmaintainable as the system evolves.
- **Persistence internals do not leak as contracts.** Table names, column names, foreign key IDs, internal surrogate keys, ORM join columns, and version/etag fields are implementation details. External APIs and inter-service contracts use DTOs with stable field names that evolve independently. Changes to persistence implementation must not silently break consumers.
- **Soft-delete is a product decision, not a default.** Soft-delete (`deleted_at`, `is_deleted`) introduces: query filter noise (every query must add `WHERE deleted_at IS NULL`), unique constraint interference, referential integrity complexity, audit log duplication, and GDPR "right to be forgotten" complications. Use it only when the business explicitly requires recoverable deletion or audit of deletions. Otherwise, hard-delete with proper archival strategy.
- **Aggregate boundaries define transaction scope.** Objects modified together in one business operation belong in the same aggregate. Objects that can be modified independently belong in separate aggregates. An overly large aggregate causes write contention; an overly small aggregate requires distributed transactions for business operations that should be atomic.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| New source-of-truth model | New entity, document, aggregate, ownership area, or stored lifecycle. | Define invariants, owner, identity, relationships, lifecycle, storage fit, and contract separation before schema or DTOs. | Entity/attribute owner, invariants, relationship/cardinality map, invalid states, query/write patterns. | `domain-object-identification`, `business-rule-extraction`, `repository-persistence` | DTO/API field polish. |
| Existing model evolution | Add/remove/rename fields, constraints, relationships, or states on stored data. | Preserve old data, compatibility, rollback, and null/default semantics while evolving the model. | Old/new model diff, compatibility class, nullable/lifecycle meaning, migration impact, rollback risk. | `data-migration-design`, `version-compatibility`, `quality-test-gate` | One-step destructive DDL. |
| Boundary separation repair | Persistence table leaks into API/event/DTO, or DTO/domain/persistence semantics drift. | Reassert source-of-truth model and mapping boundaries without exposing internals. | Boundary map, internal/public field split, mapper owner, generated/client impact. | `dto-schema-design`, `api-contract-design`, `model-boundary-mapping` | Returning ORM/persistence objects as contracts. |
| Read model or denormalization decision | Materialized view, projection, snapshot, JSON field, or copied data is proposed. | Decide source-of-truth vs derived data, staleness tolerance, rebuild path, and write amplification. | Critical queries, staleness policy, rebuild strategy, owner of derived data, rejected normalized alternative. | `search-analytics-design`, `indexing-query-optimization`, `repository-persistence` | Cache/search as source of truth. |
| Regulated, temporal, or destructive data | PII/PHI/PCI, financial ledger, audit, retention, erasure, archival, temporal history. | Model retention, deletion, auditability, reversibility, and historical truth before implementation. | Data classification, retention/deletion rule, temporal strategy, audit owner, validation report. | `security-privacy-gate`, `backup-recovery`, `data-migration-design` | Unowned soft-delete default. |
| Model closure / handoff | Final answer, review, ADR, or release note says the model is accepted, safe, compatible, or migration-ready. | Tie every model-safety claim to fresh source, graph, memory, execution, and validation evidence. | changed model-to-validation map, accepted/rejected memory, stale evidence limits, next gate. | `plan-execution-consistency`, `validation-broker`, `quality-test-gate` | Completion language without evidence mapping. |

# Industry Benchmarks

Anchor against Domain-Driven Design aggregate and repository patterns, Designing Data-Intensive Applications data-model/storage tradeoffs, CQRS/read-model discipline, 3NF/BCNF normalization, temporal modeling, GDPR erasure, HIPAA/PCI minimization, OWASP secure data handling, PostgreSQL constraint patterns, and JSON Schema validation. Keep this body focused on routing, evidence, output, and quality gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for storage-family selection, normalization/denormalization decisions, invariant enforcement examples, ownership maps, temporal/retention patterns, and detailed anti-patterns.

# Selection Rules

Select this capability when **the shape, constraints, and lifecycle of stored data** are the primary decisions. Adjacent routing:

- Prefer `dto-schema-design` when the question is the serialized transfer object structure for APIs or events.
- Prefer `api-contract-design` when defining what clients see (vs what is stored).
- Prefer `data-migration-design` when the model is changing for existing stored data.
- Prefer `relational-database` for physical storage-engine specifics (index types, partitioning, vacuum, MVCC).
- Prefer `nosql-database` for physical document model specifics (embedding strategy, sharding, TTL, consistency settings).
- Prefer `domain-impact-modeler` when assessing how a model change propagates across bounded contexts.

# Risk Escalation Rules

Escalate when: the model stores regulated data (PII/PHI/PCI/PSD2 financial); the model is the source of truth for financial account balances, audit logs, or compliance records; data deletion is irreversible and violates GDPR/CCPA requirements; the aggregate boundary change requires distributed transactions across services that cannot be made atomic; the model is shared across microservices via direct DB access (dual-write, read replica coupling); the model change requires a large backfill (> 10M rows) with no approved migration plan; a foreign key removal would silently allow orphaned records; the model stores cryptographic material (key IDs, hashes, salts) without defined access control.

# Proactive Professional Triggers

- **Signal:** a new table/document mirrors a screen, form, import file, or API response one-to-one. **Hidden risk:** UX or integration shape becomes the source of truth and domain invariants are missing. **Required professional action:** identify entities, ownership, invariants, lifecycle states, and rejected persistence/API leakage before schema acceptance. **Route to:** `domain-object-identification`, `dto-schema-design`, `api-contract-design`. **Evidence required:** entity map, invariant list, contract separation map, and validation plan.
- **Signal:** nullable field, default value, enum/status, JSON blob, or polymorphic association is added without lifecycle semantics. **Hidden risk:** invalid states and semantic drift become representable and hard to migrate. **Required professional action:** classify absent/null/unknown/not-applicable/deleted meanings and enforce constraints where feasible. **Route to:** `model-boundary-mapping`, `quality-test-gate`. **Evidence required:** null/default semantics table, invalid-state examples, constraint or service validation evidence, and residual risk owner.
- **Signal:** two services, jobs, integrations, or support tools can write the same record or attribute. **Hidden risk:** source-of-truth ambiguity, last-write-wins data loss, and graph ownership drift. **Required professional action:** assign per-attribute write authority and cross-service access protocol before model approval. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`. **Evidence required:** writer inventory, current-source confirmation, accepted/rejected prior memory, and event/API access path.
- **Signal:** denormalized read model, materialized view, copied snapshot, JSON column, or search/analytics projection is proposed as authoritative. **Hidden risk:** derived state becomes stale source of truth and writes need unowned reconciliation. **Required professional action:** decide source-of-truth vs derived data, staleness tolerance, rebuild strategy, and write amplification. **Route to:** `search-analytics-design`, `indexing-query-optimization`, `data-side-effect-flow-tracing`. **Evidence required:** query/write pattern map, staleness policy, rebuild command or report artifact, and owner.
- **Signal:** a model proposal relies on prior project memory, repository graph proximity, or a previous agent trajectory as proof of accepted data shape. **Hidden risk:** stale context misses current callers, generated artifacts, migrations, or downstream contract dependencies. **Required professional action:** confirm with current source, registry/config, tests, generated artifacts, and validation output before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, freshness limit, accepted/rejected prior evidence, and remaining unknowns.
- **Signal:** a review or handoff claims the model is safe, compatible, migration-ready, or source-of-truth aligned without a changed model-to-validation map. **Hidden risk:** silent invalid states, stale generated clients, direct DB consumers, or unverified reports survive because design reasoning is mistaken for proof. **Required professional action:** map each changed entity, attribute, relationship, constraint, read model, and ownership decision to a validator, test, report, reviewed artifact, or explicit residual risk before closure. **Route to:** `validation-broker`, `contract-testing`, `data-migration-design`, `agent-execution-discipline`. **Evidence required:** changed model-to-validation map, validator command or artifact, exit code when runnable, what evidence proves, what it does not prove, next gate, and residual risk owner.

# Critical Details

The most expensive data model mistakes are invisible at design time and catastrophic at scale:

- **The NULL problem.** A `nullable` column can mean four different things: (1) "not yet known", (2) "not applicable", (3) "deleted/removed", (4) "explicitly set to empty". Each meaning implies different business logic and query behavior. Use separate boolean flags (`is_applicable`, `is_deleted`) or separate tables for different lifecycle meanings instead of overloading nullable semantics.
- **Surrogate vs natural keys.** Surrogate keys (UUID, auto-increment) are stable and safe for internal references. Natural keys (email, SSN, product code) change in the real world and should not be primary keys used as foreign key targets. Use surrogate keys as PK; store natural keys as unique-constrained columns.
- **UUID v4 vs UUID v7 for performance.** UUID v4 is random → causes B-tree index fragmentation at high insert rates. UUID v7 (draft RFC 9562) is time-ordered → insert locality; better index performance. For PostgreSQL at high insert rates, use `gen_random_uuid()` (v4) or a time-sortable ID (ULID, UUID v7) based on insert pattern.
- **Soft-delete + unique constraints.** `UNIQUE(email)` + `deleted_at IS NOT NULL` means a deleted user's email blocks re-registration. Solution: partial unique index `CREATE UNIQUE INDEX ON users(email) WHERE deleted_at IS NULL`.
- **Polymorphic associations.** A `comments` table with `commentable_type` + `commentable_id` cannot have a foreign key constraint. Referential integrity is lost. Prefer separate junction tables (`post_comments`, `video_comments`) with proper foreign keys.
- **Temporal modeling.** For "what was the value at time T?" use bi-temporal tables: `valid_from`, `valid_to` (business validity) + `created_at` (transaction time). Overwriting current values loses history. Use SCD Type 2 (insert new row, close old row's `valid_to`) for auditable temporal data.
- **JSON columns: flexibility vs constraint.** `jsonb` in PostgreSQL offers flexible schema but no column-level constraints, no foreign keys, no column statistics for the planner. Use for genuinely schema-variable data; never as a workaround for avoiding proper schema design.
- **N+1 query patterns.** A 1:N relationship where the application fetches the parent then loops to fetch each child is an N+1 pattern baked into the model. Design the model and access layer together; use eager loading (`JOIN`, `IN` clause, or dataloader pattern) for collection relationships.
- **Write amplification in denormalized models.** Denormalized copies of data (e.g., `username` copied to every post record) require updating every copy on change. At scale, write amplification outweighs read simplification. Prefer read-time joins or materialized views with explicit staleness tolerance.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `users` table with `json_data` column containing all variable fields | No constraints; application diverges; impossible to query or index; migration requires full table scan |
| `orders` table with 12 nullable columns, no status enum | Invalid states representable; NULL means 4 different things; bugs from overloaded nullability |
| Table name `user_accounts` in API response JSON | Persistence internals in contract; rename breaks all consumers |
| `status VARCHAR(255)` with no constraint | Any string is valid status; typos silently stored; application logic diverges |
| Comments with `commentable_type / commentable_id` (polymorphic) | No FK constraint; orphaned comments accumulate; cannot join efficiently |
| Soft-delete + UNIQUE(email) | Deleted user's email permanently blocks new registration unless partial index added |
| Service B reads Service A's database directly | Tight coupling; any schema change in A breaks B silently; no ownership boundary |
| UUID v4 as clustered PK at 100K inserts/s | B-tree fragmentation; index size 2× random; IO amplification at scale |

# Failure Modes

- **Screen-shaped source of truth:** table designed from screen mockup; domain invariant `order must have at least one line item` is not enforced; empty orders become possible.
- **Overloaded nullability:** `completed_at IS NULL` means both "not started" and "cancelled" depending on undocumented convention; query logic branches diverge.
- **Unowned writer conflict:** two services write to the same column with no authority rule; last-write-wins causes data loss during concurrent updates.
- **Unconstrained state:** `status` stored as `VARCHAR` with no constraint; typo `'shiped'` is stored and dashboard aggregation silently drops 2% of orders.
- **Soft-delete uniqueness break:** soft-delete is added without partial unique index; re-registration fails for deleted users and support tickets rise.
- **Unsafe evolution:** model ships without migration plan; column add requires NOT NULL DEFAULT on PG 10 and causes deployment outage.
- **Persistence leak:** external API returns `user_id`, `table_name`, `db_schema` fields; persistence internals become public and require immediate API versioning.
- **Oversized aggregate:** `order` aggregate includes `customer`; write contention causes deadlocks under concurrent order placement.
- **Undersized aggregate:** `order_item` is a separate aggregate; placing an order requires 2-phase commit and exposes a distributed transaction bug.
- **Lost temporal truth:** temporal query ("what was the price on 2025-01-01?") is impossible because price is overwritten in place; historical records are lost.
- **Poor key locality:** UUID v4 clustered PK with 200K inserts/s fragments indexes; query performance degrades 3x over 6 months.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 data-model selection, boundary, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete model proposal, when invariants/ownership/migration coverage is uncertain, or before implementation starts. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when storage-family choice, normalization tradeoff, constraint pattern, ownership map, temporal model, retention/deletion, or anti-pattern detail is needed. Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on changed model-to-validation mapping, graph/memory/execution freshness, tool permission boundaries, old/new reader compatibility, or final handoff readiness. Use [examples/example-output.md](examples/example-output.md) only when the expected proposal shape is unclear. Do not load references for pure routing or trivial wording work where the output contract and quality gate are sufficient.

# Output Contract

Return a data model proposal with:

- `mode_selected` (new source-of-truth, existing model evolution, boundary separation repair, read-model decision, regulated/temporal/destructive data)
- `boundaries_inspected` (source paths, registry/config, migrations, generated artifacts, tests, existing models, and prior memory accepted or rejected)
- `source_evidence` (specific current-source observations, not inferred architecture memory)
- `entities_or_documents` (per entity: name, table/collection, purpose, storage type)
- `ownership` (per entity/attribute: owning service, write authority, cross-service access protocol)
- `invariants` (per entity: rules that must always be true; invalid state description; enforcement: DB constraint vs application)
- `attributes` (per attribute: name, type, nullable, default, constraint, lifecycle meaning)
- `relationships` (per relationship: entity A, entity B, cardinality, foreign key strategy, nullability, referential action)
- `lifecycle_states` (per entity: valid states, allowed transitions, check constraint SQL)
- `query_patterns` (3-5 critical queries with access pattern, index strategy, estimated selectivity)
- `write_patterns` (write rate estimate, update-heavy vs append-only, concurrent write risk)
- `constraints` (UNIQUE, CHECK, FK, EXCLUDE constraints; partial index for soft-delete if used)
- `retention_and_deletion` (retention period, archival strategy, GDPR/CCPA deletion approach, audit log requirements)
- `migration_impact` (columns safe to add nullable-first, columns requiring dual-write, columns that are breaking)
- `read_models` (CQRS projections or materialized views: staleness tolerance, rebuild strategy)
- `contract_separation` (API-facing DTO names and fields vs internal table names; explicit mapping)
- `normalization_level` (3NF, BCNF, or justified denormalization with staleness policy)
- `changed_model_to_validation_map` (each changed entity/attribute/relationship mapped to unit, integration, migration, contract, or manual validation)
- `reuse_and_placement_rationale` (existing model/reference reused, extension location, rejected locations, and why no new shared abstraction was added)
- `behavior_preservation` (old rows, old writers, old readers, old generated clients, and old queries that remain valid)
- `validation_evidence` (commands, reports, fixtures, screenshots, or review artifacts that were run and what they prove)
- `handoff_boundaries` (which decisions move to migration, DTO/API contract, repository, security, reliability, or release gates)
- `evidence_limits` (what was not inspected, what remains unknown, and residual risk owner)
- `open_decisions` (unresolved: aggregate boundary, ownership, temporal modeling approach)

# Evidence Contract

Close a data-model-design proposal only when these answers are concrete:

- **Current source inspected:** name the files, schemas, migrations, generated artifacts, registry/config entries, tests, docs, and prior memory that were checked. If no current implementation exists, say that explicitly.
- **Graph and memory freshness:** state which repository graph or project-memory facts were accepted, which were rejected as stale or irrelevant, and which source reads confirmed them.
- **Invariant proof:** for each critical invariant, identify the enforcement layer, validation command or review artifact, and the failure mode covered.
- **Compatibility proof:** state how old persisted data, old writers, old readers, old API/DTO clients, generated code, and reporting/query consumers behave after the model change.
- **Validation result:** include command names and pass/fail status. Do not claim completion from design reasoning alone.
- **What evidence does not prove:** call out untested scale, concurrency, migration-duration, privacy, or downstream-contract assumptions.
- **Next gate:** name the next capability or human review needed when migration, API, DTO, security, reliability, or release evidence is outside this capability.

# Quality Gate

The data model passes only when:

1. All domain invariants are stated; each is enforced at DB layer (constraint) or at minimum at service layer with documented rationale for not using DB constraint.
2. Every entity has a single named write-authority; cross-service access is via API/event not direct DB.
3. Nullable columns have explicit semantic meaning; no overloaded nullability.
4. All status/enum fields are constrained to valid values at the DB layer.
5. Query patterns are documented with index strategy; no obvious N+1 or full-table-scan pattern uncovered.
6. Migration impact is assessed; no single-step breaking DDL on hot tables.
7. Persistence internals (table names, column names, internal IDs) are not in the external API contract.
8. Lifecycle state machine has invalid-state constraints enforced at DB layer.
9. Retention and deletion policy is documented; GDPR/CCPA deletion is possible without breaking historical integrity.
10. Aggregate boundary matches transaction scope; no cross-aggregate atomicity without explicit distributed transaction strategy.

# Used By

- data-api-contract-changer
- domain-impact-modeler

# Handoff

Hand off to `data-migration-design` for migration planning on existing data; `dto-schema-design` for API transfer shapes; `api-contract-design` for client-visible behavior; `relational-database` for physical relational tuning; `nosql-database` for document model physical design; `domain-impact-modeler` for cross-context impact analysis.

# Completion Criteria

The capability is complete when **the data model encodes domain invariants with DB-level enforcement, supports known access patterns without emergency rewrites, has clear ownership per attribute, has a migration-safe evolution path, and cleanly separates persistence internals from API contracts** — and every invalid state that the business cares about is unrepresentable in the schema.
