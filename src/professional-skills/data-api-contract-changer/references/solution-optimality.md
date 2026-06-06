# Solution Optimality Self-Check — Data & API Contract Changer

Compiled from foundation capability `solution-optimality-evaluation`. Apply to every
contract change that introduces a new schema, versioning strategy, migration, or API
endpoint. Loaded on demand per the skill's Reference Loading Policy.

**Three-Challenge Rule** — answer all three before finalizing any contract design:
1. **Why this approach?** State the concrete reason (not "it's the common pattern" or "Stripe does it this way"). What specific consumer requirement or operational constraint drives this design?
2. **Is this the simplest sufficient design?** Before adding a version, a compatibility shim, or a migration strategy, confirm it is actually needed. An additive change requires none of these.
3. **What is the strongest alternative, and why is it rejected?** Name it. Reject it with a specific cost ("requires coordinated consumer deployment", "adds a JOIN per request", "breaks 3 known consumers without a migration window").

**Performance Dimension Checklist** — evaluate each or declare N/A with a one-line rationale:

| Dimension | Required Question | Contract-Specific Failure Mode |
|---|---|---|
| **CPU** | Does the versioning compatibility layer add serialization/transformation overhead per request? Is the overhead acceptable at target RPS? | A per-request field-mapping shim between v1 and v2 adds 5ms CPU at 1k RPS — 5 CPU-seconds per second of sustained load |
| **Memory** | Does the response payload size increase with the new schema? Are unbounded list responses now possible? Is a response object retained in memory across the request lifecycle? | New `include=children` expansion parameter returns entire subtrees with no depth limit; response size grows unbounded with data volume |
| **Network** | Does the new schema add nested objects that trigger N+1 database queries per expansion? Is the response payload size budgeted (≤ 50KB for standard API responses)? | `?include=orders.items.product` triggers 3 nested N+1 queries; no field projection available to limit payload size |
| **Disk** | What is the migration I/O cost (rows touched, index rebuild size, WAL amplification)? Is the migration scheduled during a low-traffic window? | `ADD COLUMN NOT NULL DEFAULT` in PostgreSQL rewrites every row; on a 50M-row table this holds an exclusive lock for minutes |
| **Locks / Contention** | Does the migration require an exclusive table lock? What is the maximum lock hold time at production data volume? Can a non-locking migration strategy (shadow column + background copy) be used instead? | `ALTER TABLE ADD COLUMN NOT NULL` without a default causes table rewrite + exclusive lock on PostgreSQL < 11 |
| **TPS / QPS** | Does the new endpoint or schema version add meaningful per-request overhead (extra query, extra serialization step, extra validation pass)? Is the overhead quantified? | Each versioned endpoint runs field-compatibility validation on every response — 0.5ms overhead × 2k RPS = 1 CPU-second/second added |
| **Parallelism** | Can migration data backfill be parallelized safely? Is there a shard or partition strategy for large data migrations? | Backfill running as a single sequential transaction on 100M rows blocks other queries and takes 4 hours |
| **Concurrency** | Is the migration safe to run while the application is live (online migration)? Is there a version skew window where old and new code coexist with the same schema? | Migration removes a column that old code still reads — old pods fail during the blue-green deployment overlap window |
| **Response Latency** | What is the P99 latency budget for the new or changed endpoint? Is it validated under realistic query load with the migrated schema? | Latency was only measured with 1,000 rows in staging; the production table has 80M rows and the query plan changes with the new index |

**Additional Professional Considerations for Contract Changes:**
- **Pagination is always required for list endpoints**: An endpoint that returns all records without pagination is a latency time bomb as data grows. Cursor-based pagination is preferred over offset for large datasets (offset requires scanning all preceding rows).
- **Field expansion depth limits**: Any `include` or `expand` parameter must have a maximum depth limit and a maximum number of expanded objects enforced at the API layer — not just documented.
- **Index justification required for every new filter/sort parameter**: Every new `?sort=field` or `?filter[field]=value` that is not backed by an index will trigger a full table scan at production data volume. Require index design before the parameter ships.
- **Deprecation is a commitment, not a comment**: A deprecated field or endpoint requires a sunset date, a replacement, a migration guide, and consumer notification before the deprecation is announced. Deprecation without these is deletion without warning.
- **Migration rollback must be executable in ≤ 5 minutes**: A rollback migration that requires 30 minutes to execute is not a rollback — it is a recovery procedure. Design migrations to be rollback-fast or accept that rollback is not possible and require higher sign-off.
