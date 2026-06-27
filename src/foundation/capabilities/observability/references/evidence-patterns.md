# Observability Evidence Patterns

Use this reference when observability closure depends on repository graph, project memory, execution trajectory, validation freshness, dashboard/runbook evidence, tool permission boundaries, or a changed-signal-to-validation map. Keep it as an evidence map, not a second observability tutorial.

## Changed-Signal-To-Validation Map

| Claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| SLI/SLO is measurable | User journey, metric name, formula, labels, window, owner, dashboard panel, and current query or config path. | The named journey has a measurable user-impact signal. | Historical baseline accuracy, production scale, or all client segments are proven. |
| Structured log is safe and queryable | Field list, redacted/excluded fields, correlation or trace binding, sample query, and current source/config path. | Operators can find the inspected event without exposing sensitive fields. | Every caller, debug path, log sink, or retention policy is safe unless inspected. |
| Metric labels are bounded | Label list, allowed values or cardinality estimate, rejected high-cardinality fields, and metric query. | The inspected metric is unlikely to overload the telemetry backend through obvious unbounded labels. | Production cardinality, tenant skew, or backend retention cost is proven. |
| Trace continuity is current | Ingress extraction, outbound injection, async/job propagation point, span names, and trace lookup or source proof. | The inspected path can correlate logs, metrics, and spans across the named boundary. | Sibling async flows, provider-specific propagation, or sampling behavior is complete. |
| Alert and dashboard are actionable | Alert query, threshold, severity, owner, runbook action, dashboard path, and synthetic/sample event when feasible. | The inspected operator workflow can detect and start remediation for the named symptom. | On-call behavior, alert fatigue, or incident response effectiveness is proven. |
| Validation is fresh | Command or query, working directory or environment, exit code/outcome, report/artifact path, and final-edit freshness. | Evidence was produced after the final material change for the mapped signal. | Later source/config/dashboard/generated/report edits are covered. |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, old dashboards, incident notes, generated docs, prior validation, and execution trajectory as discovery inputs until current source/config/query evidence confirms them.
- Accept prior "dashboard exists", "alert covers this", "trace propagation already works", or "runbook owner is current" claims only when current metric names, labels, spans, runbook owner, and changed paths still match.
- Reject or downgrade memory that lacks date, owner, environment, query/config path, changed-signal scope, command outcome, or residual-risk owner.
- Mark evidence stale after edits to log fields, metric names or labels, span names, trace propagation, alert expressions, dashboards, runbooks, generated docs, reports, build outputs, or validation mappings.
- Map every final observability confidence claim to a current command, metric query, log query, trace lookup, alert check, dashboard path, synthetic event, owner approval, or explicit not-verified residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, graph search, report inspection, and markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps. |
| Local validators, tests, builds, alert-rule linters, and dashboard/config checks | State-mutating only for reports, caches, temp files, dist/build artifacts, or local test fixtures; cite log path, command, exit code, and cleanup. |
| Synthetic telemetry event, fixture generation, dashboard export, or generated doc refresh | State-mutating development action; record source-of-truth input, generated output owner, redaction rule, diff review, and rollback path. |
| Live telemetry query, connector export, cloud console, deploy, migration, rollback, or production alert change | High-risk or connector-scoped action; require permission or sandbox proof when available, redact tenant/user/secret-bearing values, and state retention limits. |

## Handoff Evidence Shape

```yaml
observability_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_signal_to_validation_map:
    - signal: ""
      source_or_config_path: ""
      validation_command_or_query: ""
      exit_code_or_status: ""
      artifact_or_dashboard: ""
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
