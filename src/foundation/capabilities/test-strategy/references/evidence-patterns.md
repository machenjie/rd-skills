# Test Strategy Evidence Patterns

Use this evidence map for a named changed-code-to-test, freshness, omission, command-signal, affected-test, or admissibility claim; keep stale, partial, flaky, retried, and skipped evidence explicit for `quality-test-gate`.

## Changed-Code-To-Test Map

| Claim | Minimum current evidence | Proves / limit |
| --- | --- | --- |
| Behavior covered | Changed path, behavior, acceptance/risk, level, command, owner. | Runnable obligation; not hidden consumers/branches/production-only conditions. |
| Failure covered | Denied/invalid/conflict/timeout/retry/rollback/partial case and result. | Named failure differs from success; not every provider taxonomy. |
| Compatibility covered | Consumers, contract diff, generated check, old/new fixture. | Inspected consumers; not unknown externals or stale clients. |
| Migration integrity covered | Forward/rollback, representative shape, integrity assertion, artifact. | Inspected recovery; not production volume, lock, RTO, or every skew. |
| Affected scope bounded | Changed paths, transitive dependents, generated/cache inputs, required signals. | Strategy obligations; not exact entrypoints, combined coverage, or fallback. |
| Evidence fresh | Command, directory, status, summary, artifact, final-edit freshness. | Post-edit mapped evidence; not later edits. |
| Omitted level owned | Reason, compensating evidence, release consequence, owner, reopen trigger. | Explicit omission; not permanent lack of value. |

## Freshness And Permission Rules

- Treat repository inspection, prior evidence, CI, coverage notes, reports, and memory as discovery until current source confirms them.
- Reopen after relevant source, test, fixture, schema, migration, lockfile, CI, report, generated-input, or command-mapping edits.
- Accept prior coverage claims only when current paths, tests, generated inputs, CI, and reports still match; otherwise record `not verified` and proof limits.
- Bind final confidence to a command, test, validator, report, diff, review artifact, approval, or explicit not-run risk.
- For regeneration, record source input, output owner, diff review, and rollback.
- External, deploy, migration, restore, or rollback commands need authority, bounded effects, sandbox/dry-run where available, recovery, redaction, and stop.
- Telemetry/audit/export evidence stays read-only or approved-connector-scoped with sensitive-value redaction and retention limits.

## Anti-Patterns

Reject catalog-, coverage-, broad-suite-, mock-, or manual-only proof without a task-specific mechanism and oracle.
