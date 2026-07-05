# Data Migration Evidence Patterns

Use this reference when migration closure depends on graph, memory, execution output, validation freshness, tool permission boundaries, or production evidence limits. Keep it as an evidence map, not a second migration tutorial.

# Migration-To-Validation Map

| Migration claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Current schema and migration ledger are known | Schema files, applied migration list, generated clients, and migration checksums inspected | The plan targets the inspected source state | Hidden manual DB drift or uninspected downstream stores |
| Old and new code can coexist | Expand/migrate/contract compatibility matrix plus reader/writer inventory | Inspected versions can run in the stated deployment order | Unknown consumers, mobile lag, or external reports are safe |
| DDL avoids unsafe locks | Lock class, online DDL choice, timeout/abort threshold, and representative dry-run or explicit not-verified limit | The selected DDL path has a bounded lock strategy | Actual production lock contention or peak traffic impact |
| Backfill is resumable | Batch, checkpoint, idempotent predicate, interruption/resume test, and progress metric | Tested job can resume without double-processing the covered rows | Sparse partitions, all tenant distributions, or full production runtime |
| Validation covers affected data | Full-count, partition, or tenant validation query with expected and actual counts | Inspected affected rows satisfy the declared invariant | Future writes, late CDC events, or hidden consumer transforms |
| Rollback tier is credible | Per-phase rollback tier, command/test/report, owner signoff, and point-of-no-return note | The named phase has a reviewed recovery path | Restore RTO, provider SLA, or manual runbook reliability unless rehearsed |
| Destructive cleanup is safe | Caller search, generated artifact diff, zero-use telemetry gate, backup/restore evidence, and signoff | Inspected old readers/writers are gone before deletion | Uninstrumented jobs, ad hoc queries, or offline archives are safe |
| Cross-system cutover is bounded | Source-of-truth decision, CDC lag, reconciliation diff, replay/abort plan, and post-cutover validation | Source/target divergence is measured for the inspected cutover | Long-tail event order, all regions, or uninspected repair jobs |
| Release watch can detect harm | Lag, lock wait, error, throughput, duration, and completeness metrics with owner and threshold | Operators can see expected migration failure signals | Thresholds are sufficient for every production seasonality pattern |

# Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, previous migration notes, runbooks, dashboards, and old validation reports as discovery inputs until current source confirms them.
- Accept a previous "no readers", "backfill done", "safe DDL", "rollback tested", or "ledger repaired" claim only when the schema, migration scripts, generated clients, reports/jobs, row volumes, deployment order, and validation command still match current state.
- Mark evidence stale after edits to migration files, schema, generated clients, fixtures, release sequence, feature flags, validation queries, reports, or build/install outputs.
- Record inspected and skipped consumers: application readers/writers, generated clients, reports, jobs, ETL, dashboards, external integrations, and manual query surfaces.
- Map every final migration-safety claim to a command, test, validator, report, migration dry run, telemetry query, restore rehearsal, or explicit not-run residual risk.

# Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, `rg`, parser scripts, report inspection | Read-only local shell action; cite searched paths and avoid full output dumps |
| Local validators and builds | State-mutating only for reports/dist/build artifacts; cite log path and exit code |
| Migration dry run against local or throwaway DB | State-mutating test action; record dataset, cleanup, reset, and absence of production credentials |
| Production DB, CDC, backup, restore, cloud, or deploy command | High-risk state-mutating action; require permission, dry-run when available, rollback/forward-fix path, stop condition, and redaction rule |
| Telemetry, dashboard, or audit export | Read-only or connector-scoped; redact tenant/user/secret-bearing values and state retention limits |

# Handoff Evidence Shape

```yaml
migration_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_migration_to_validation_map:
    - migration_decision: ""
      validator_or_test: ""
      exit_code: ""
      artifact_or_report: ""
      proves: ""
      does_not_prove: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
