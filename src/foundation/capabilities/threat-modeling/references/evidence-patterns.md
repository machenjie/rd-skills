# Threat Modeling Evidence Patterns

Use this reference when closure depends on repository graph, project memory, execution trajectory, validation freshness, command output, generated artifacts, tool permission boundaries, or a threat-to-validation map. Keep it as an evidence map, not a second threat-modeling tutorial.

## Threat-To-Validation Map

| Claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Entry points are enumerated | Current routes/controllers/resolvers/jobs/webhooks/uploads/gateways, generated artifacts, and deployment/IaC exposure inspected. | The named reachable surfaces were reviewed for threat modeling. | Dynamic routes, external consumers, or hidden deployments are safe unless inspected. |
| Asset classification is current | Data fields, secret/token/key material, tenant/admin/payment/regulated scope, owner, and retention or DPIA trigger. | The model knows what must be protected. | All downstream copies, logs, exports, or analytics stores are covered unless traced. |
| Trust boundary is validated | Source and sink paths, caller identity, tenant/object scope, input/output trust, and control location. | The inspected crossing has a named protection point. | Sibling boundaries or future architecture changes are protected. |
| Mitigation is implemented | Code/config/policy location, owner, status, test/review artifact, command/report, exit code, and freshness. | The named control exists and was verified for the inspected threat. | Other actors, assets, environments, or exploit variants are safe. |
| Monitoring is deployed | Log/audit/metric/alert/runbook source, safe fields, owner, and abuse signal. | Exploit attempts for the named path have a detection plan. | Detection latency, production tuning, or incident response has been proven unless tested. |
| Residual risk is accepted | Severity, compensating control, owner, rationale, expiry, release condition, and reopen trigger. | The remaining risk is explicit and accountable. | The risk may remain acceptable after scope, data, actor, or threat landscape changes. |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, prior threat models, scanner output, architecture notes, generated artifacts, and execution traces as discovery inputs until current source confirms them.
- Accept prior "boundary safe", "auth covered", "no external exposure", or "mitigation implemented" claims only when current paths, configs, generated files, tests, and reports still match.
- Reject or downgrade memory that lacks date, owner, scope, inspected paths, changed graph delta, validation command, or residual-risk owner.
- Mark evidence stale after edits to routes, middleware, authorization policy, schemas, generated clients, workers, queues, uploads, IaC, secrets/config, reports, or validation mappings.
- Map every final security confidence claim to a source path, control location, command, test, scanner/report, monitoring artifact, owner approval, or explicit not-run residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, graph search, report inspection, markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps. |
| Local validators, tests, security linters, and builds | State-mutating only for reports, caches, temp files, dist/build artifacts, or local test data; cite log path, command, exit code, and cleanup. |
| Secret scan, dependency scan, IaC plan, policy simulation, or generated artifact regeneration | Security-sensitive development action; record tool, input scope, redaction rule, diff review, and rollback/revert path. |
| External sandbox, live provider, connector, cloud, deploy, migration, backup, restore, or rollback command | High-risk action; require permission, dry-run/sandbox proof, stop condition, rollback/forward-fix path, and secret/output redaction. |

## Handoff Evidence Shape

```yaml
threat_model_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  threat_to_validation_map:
    - threat_id: ""
      actor: ""
      asset: ""
      entry_point: ""
      trust_boundary: ""
      control_location: ""
      validation_command_or_artifact: ""
      exit_code_or_status: ""
      monitoring_signal: ""
      proves: ""
      does_not_prove: ""
      owner: ""
      freshness: ""
  residual_risks:
    - threat: ""
      severity: ""
      rationale: ""
      compensating_control: ""
      owner: ""
      expiry_or_review_date: ""
      next_gate: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
```
