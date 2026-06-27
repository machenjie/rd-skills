# Data Model Evidence Patterns

Use this reference when model closure depends on graph, memory, execution output, validation freshness, tool permission boundaries, compatibility claims, or production evidence limits. Keep it as an evidence map, not a second data modeling tutorial.

# Model-To-Validation Map

| Model claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Current source-of-truth model is known | Schema/model files, migrations, generated clients, repository methods, and config/registry entries inspected | The proposal targets the inspected source state | Hidden manual DB drift, uninspected reports, or external consumers are safe |
| Entity ownership is singular | Entity/attribute owner map plus current writer inventory from services, jobs, imports, and support tools | Inspected writers follow the declared authority boundary | Future integrations or uninspected manual writes cannot bypass ownership |
| Invariant is enforceable | DB constraint, schema validation, service guard, or reviewed residual-risk decision tied to each invariant | The inspected invariant has a named enforcement layer | Concurrent edge cases, storage-specific lock behavior, or production cardinality are fully safe |
| Null/default semantics are intentional | Null/default meaning table plus old-row, create-path, update-path, and query fixture or review artifact | Inspected readers can distinguish absent, unknown, not-applicable, deleted, and default states | Every downstream analytics/reporting interpretation is correct |
| Relationship cardinality is valid | Cardinality map, FK/junction decision, referential action, cycle/depth rule, and representative query path | Inspected relationship shape preserves referential meaning | Production data skew or all recursive traversal costs are bounded |
| Read model remains derived | Source-of-truth owner, staleness tolerance, rebuild command/report, and reconciliation owner | Inspected projection can be rebuilt and is not the authoritative write surface | All late events, regional lag, or consumer cache behavior is covered |
| Persistence/API boundary is clean | DTO/domain/persistence mapping, generated-client diff, and no direct ORM/entity exposure review | Inspected external contract does not depend on table internals | Unknown consumers or undocumented direct database reads are absent |
| Existing model evolution is compatible | Old/new model diff, old readers/writers, old rows, generated clients, report/jobs, and migration handoff inspected | Inspected version window has a compatibility path | Live migration duration, rollback execution, or uninspected mobile/client lag is safe |
| Regulated or temporal data is modeled | Data classification, retention/deletion/audit rule, temporal strategy, and security/privacy owner | Inspected fields have a reviewable retention and history model | Legal approval, restore RTO, or full compliance packet is complete |

# Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, prior model notes, old ADRs, generated artifacts, dashboards, and earlier validation reports as discovery inputs until current source confirms them.
- Accept a previous "single writer", "no direct DB consumers", "DTO boundary is clean", "null is harmless", or "projection is derived" claim only when the current schema, repositories, generated clients, jobs, reports, migrations, and tests still match it.
- Mark evidence stale after edits to schema/model files, migrations, generated clients, DTO mappers, repository methods, fixtures, validation queries, reports, build/install outputs, or registry/routing rules.
- Record inspected and skipped consumers: application readers/writers, jobs, imports, reports, ETL, dashboards, generated clients, external integrations, support tooling, and manual query surfaces.
- Map every final model-safety claim to a command, test, validator, report, schema diff, generated-client diff, review artifact, or explicit not-run residual risk.

# Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, `rg`, `find`, parser scripts, report inspection | Read-only local shell action; cite searched paths and avoid full output dumps |
| Local validators and builds | State-mutating only for reports/dist/build artifacts; cite log path and exit code |
| Local schema generation, migration dry run, or fixture DB reset | State-mutating test action; record dataset, cleanup/reset, and absence of production credentials |
| Production DB, migration, backup, restore, cloud, or deploy command | High-risk state-mutating action; require permission, dry-run when available, rollback/forward-fix path, stop condition, and redaction rule |
| Telemetry, dashboard, audit, or report export | Read-only or connector-scoped; redact tenant/user/secret-bearing values and state retention limits |

# Handoff Evidence Shape

```yaml
model_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_model_to_validation_map:
    - model_decision: ""
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
