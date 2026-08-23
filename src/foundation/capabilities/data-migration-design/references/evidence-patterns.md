# Data Migration Evidence Patterns

Use this map to close migration evidence and proof limits.

## Claim Evidence Map

| Claim | Minimum current evidence | Proof / limit |
| --- | --- | --- |
| Source known | Schema, ledger/checksums, generated clients, inspected stores. | Inspected state; excludes manual drift or unseen downstream stores. |
| Versions coexist | Deployment matrix and reader/writer inventory. | Named versions/order; excludes unknown consumers, mobile lag, or external reports. |
| DDL lock bounded | Lock class, online mode, abort threshold, representative dry run or `not_verified`. | Selected strategy; excludes production contention or peak impact. |
| Backfill resumes | Batch, checkpoint, idempotent predicate, resume test, progress signal. | Covered rows; excludes sparse partitions, tenant distributions, or full runtime. |
| Invariant holds | Full, partition, or tenant query with expected/actual counts. | Declared affected data; excludes future writes, late CDC, or hidden transforms. |
| Recovery credible | Phase tier, command/test/report, owner, point of no return. | Reviewed path; excludes restore RTO, provider SLA, or manual reliability without rehearsal. |
| Cleanup safe | Caller search, generated diff, zero-use telemetry, backup/restore evidence, signoff. | Inspected readers/writers gone; excludes uninstrumented jobs, ad hoc queries, or archives. |
| Cutover bounded | Source authority, CDC lag, reconciliation diff, replay/abort, post-cutover validation. | Measured cutover; long-tail order, uninspected regions, and repair jobs remain unproved. |
| Watch detects harm | Lag, locks, errors, throughput, duration, completeness, owner, thresholds. | Expected failures visible; seasonal production behavior remains unproved. |

## Freshness And Scope

- Confirm prior claims against current schema, migrations, clients, jobs, reports, volumes, order, flags, fixtures, commands, and build/install outputs; relevant edits reopen proof.
- Record inspected/skipped readers, writers, clients, reports, jobs, ETL, dashboards, integrations, and manual queries.
- Bind final safety claims to a command, test, validator, report, dry run, telemetry query, restore rehearsal, or explicit not-run risk.

## Tool Authority

- For local/throwaway data, record dataset, cleanup, reset, and absence of production credentials.
- Production database, CDC, backup, restore, cloud, or deploy action requires permission, available dry run, recovery, stop, and redaction.
- Telemetry, dashboard, or audit export requires tenant, user, and secret redaction plus retention limits.

## Anti-Patterns

- Couple schema change, full backfill, consumer cutover, and destructive cleanup into one irreversible mutation.
- Treat successful statements, copied row counts, or absence of errors as proof that business invariants survived.
- Retry non-idempotent conversion blindly or let backfill and live writers race without an authority rule.
