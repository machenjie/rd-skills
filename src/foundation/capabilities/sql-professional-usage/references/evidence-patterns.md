# SQL Evidence Patterns

Use this reference when SQL closure depends on repository graph, project memory, execution trajectory, validation freshness, query-plan proof, migration/lock evidence, injection proof, tool permission boundaries, or changed-surface-to-validation mapping. Keep it as an evidence map, not a SQL tutorial.

## Changed-SQL-Surface-To-Validation Map

| SQL claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Query shape is correct | Current SQL/ORM call site, parameters, tenant/object predicates, expected cardinality, boundary fixtures, and result-shape test | The inspected query returns the expected shape for named fixtures and predicates | All tenants, reports, historic data, or application consumers are covered |
| Plan and index are acceptable | Engine/version, representative row count or stats source, `EXPLAIN`/plan artifact, index rationale, and write-cost note | The inspected query uses the declared access path for the measured data shape | Production cardinality, future stats drift, cache warmth, or replica lag is proven |
| Injection boundary is safe | Parameter binding proof, generated SQL or driver call review, identifier allowlist, malicious-input test, and same-pattern scan | The named value/identifier boundary avoids string-composed SQL for inspected paths | All query-builder branches, admin reports, or downstream SQL consumers are safe |
| Transaction and lock risk is bounded | Transaction map, isolation level, lock class/order, retry/idempotency behavior, and concurrency test or not-run owner | The inspected write path has a reviewed consistency and lock model | Every scheduler interleaving, deadlock shape, or production contention is covered |
| Migration is compatible | Expand/migrate/contract phases, caller search, row count, lock impact, forward/rollback command, and validation query | The inspected migration can be staged and checked under declared assumptions | All old/new deploy skew, replicas, online DDL limits, or backfill volume is proven |
| Prior SQL evidence is fresh | Current source/schema/migration/generated SQL/telemetry paths, accepted/rejected memory, command/report path, and final-edit freshness | The prior SQL claim still matches inspected current files | Later schema edits, hidden generated SQL, or uninspected telemetry consumers are covered |

## Evidence Quality Labels

- **Strong evidence**: current source/schema/migration inspected, command or artifact named, exit code or review status recorded, final-edit freshness stated, data-shape limits named, and proof limits named.
- **Weak evidence**: dev-data timing, syntax success, ORM use without generated SQL review, old slow-query report, style guide citation, or memory claim without current schema/source.
- **Missing evidence**: no parameterization proof, no plan artifact, no row count, no migration rollback, no lock analysis, no fixture for NULL/timezone/money/tenant boundary, or no owner for not-run validation.
- **Invalid evidence**: string-composed SQL as proof, `EXPLAIN` without relevant predicate/data shape, forward-only migration as compatibility proof, stale generated query, or inaccessible report.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Source reads, schema/migration inspection, generated SQL review, report review, and local lint | Read-only local action; cite searched paths and avoid full output dumps. |
| Query-plan command, Testcontainers/integration test, migration dry-run, fixture generation, sqlfluff, and report refresh | State-mutating only for local test databases, reports, temp files, or fixtures; cite command, exit code, artifact path, data scope, and cleanup. |
| Production/staging query execution, migration, backfill, lock inspection on live database, cloud console, or credential-backed connector | High-risk state-mutating or sensitive read action; require explicit scope, redaction, rollback/forward-fix path, stop condition, and retention boundary. |

## Handoff Evidence Shape

```yaml
sql_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_sql_surface_to_validation_map:
    - surface: ""
      risk: query_shape | plan_index | injection | transaction_lock | migration | freshness
      command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      freshness: fresh | stale | partial | not_run
      owner: ""
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
