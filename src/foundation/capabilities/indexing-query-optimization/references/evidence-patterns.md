# Indexing Query Optimization Evidence Patterns

Use this reference when query/index closure depends on project memory, repository graph, execution trajectory, validation freshness, tool permission boundaries, or production evidence limits. Keep it as an evidence map, not a second indexing tutorial.

# Changed-Query-To-Validation Map

| Query or index claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Target query is current | SQL text or ORM builder, repository/service call site, schema/index definitions, parameters, and caller frequency inspected | The optimization targets the inspected read path | Hidden ad hoc SQL, reporting jobs, or generated queries are covered |
| Plan bottleneck is real | Representative `EXPLAIN` or engine plan plus row counts, buffer/read signals, sort/join details, and data volume | The inspected plan explains the observed slow path | Peak production contention, cache warmth, or every parameter distribution is proven |
| Proposed index serves one named query | Index columns, order, partial condition, include columns, and named query are mapped together | The index has a concrete read beneficiary | The index is worth keeping after traffic changes |
| Composite order is justified | Equality/range/sort predicates, selectivity or cardinality, stable tie-breaker, and rejected column orders | The selected order matches the inspected access pattern | Future filters or alternate sort orders are optimal |
| Pagination is bounded | Table size, ordering columns, cursor/tie-breaker contract, and depth behavior are stated | The selected pagination strategy avoids the inspected deep-scan failure | Client compatibility or all UI/API semantics are safe |
| Write cost is acceptable | Write rate, index count, storage growth, maintenance/vacuum cost, and read frequency/SLO budget | The read benefit has been weighed against inspected write pressure | Production write spikes or long-term storage cost are fully known |
| Build/drop path is safe enough to propose | Online/concurrent method, lock behavior, rollback or disable path, observation window, and owner | The change has a bounded release path for the inspected table | Real production lock contention or operator response is guaranteed |
| Validation is fresh | Command, working directory or environment, exit code, report/artifact path, and final-edit freshness | Evidence was produced after the material query/index change | Later source, fixture, report, or build edits are covered |

# Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, prior agent runs, issue history, slow-query dashboards, and old validation reports as discovery inputs until current source and plan evidence confirm them.
- Accept a prior "index exists", "query is covered", "offset is acceptable", "N+1 was fixed", or "build is online" claim only when the current SQL/ORM shape, schema/index definitions, table size, statistics, deployment path, and validation command still match.
- Mark evidence stale after edits to repository methods, query builders, generated SQL, schema/index files, migrations, seed/fixture volume, validation commands, reports, build outputs, telemetry queries, or pagination contracts.
- Record inspected and skipped query surfaces: repository call sites, raw SQL, ORM scopes, reports, background jobs, dashboards, generated clients, external consumers, and manual analytics surfaces.
- Map every final optimization claim to a current command, plan, telemetry query, benchmark artifact, source path, owner approval, or explicit not-verified residual risk.

# Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, repository graph search, report inspection, and markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps |
| Local validators, tests, builds, and synthetic benchmarks | State-mutating only for reports, caches, temp files, dist/build artifacts, or local test fixtures; cite log path, command, exit code, and cleanup |
| Local database plan or benchmark command | State-mutating or data-reading test action; record dataset, schema version, parameters, cleanup, and absence of production credentials |
| Production DB plan, index build/drop, telemetry export, deploy, or rollback command | High-risk or connector-scoped action; require permission, dry-run when available, stop condition, rollback/forward-fix path, owner, and redaction rule |

# Handoff Evidence Shape

```yaml
indexing_query_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_query_to_validation_map:
    - query_or_index_decision: ""
      source_path_or_plan_artifact: ""
      validator_or_test: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
      freshness: ""
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
