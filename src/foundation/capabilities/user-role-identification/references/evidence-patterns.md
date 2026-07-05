# User Role Identification Evidence Patterns

Use this reference when role-inventory closure depends on current source evidence, repository graph, project memory, execution trajectory, validation freshness, tool permission boundaries, or role-to-validation mapping. Keep it as an evidence map, not a second actor-modeling guide.

## Role Claim-To-Evidence Map

| Role claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Actor exists in the current change | Brief, route/job/webhook/UI entry, source path, policy/doc/test reference, and excluded actor list | The named actor participates in the inspected surface | All adjacent support, admin, machine, or external actors are covered |
| Actor authority is bounded | Subject, resource, action, scope, denied action, tenant/object boundary, and owner | The inventory can feed permission modeling | Enforcement, query scoping, or auth implementation already exists |
| Data visibility is safe to hand off | Visible fields, hidden fields, export/aggregate limits, related-object traversal, and source evidence | Reviewers know what each actor may and may not see | Privacy review, production permission state, or live data access is complete |
| Service or job actor is least privilege | Owner, purpose, credential/auth method, tenant/job/run scope, audit field, and review cadence | Machine blast radius is explicit | Credential rotation, anomaly alerting, or integration reliability is proven |
| External actor trust is explicit | Authentication method, trusted claims, rejected claims, replay/idempotency need, failure behavior, and contract owner | Provider or consumer assertions are bounded | Full integration, signature verification, or provider SLA is verified |
| Support/admin access is purpose bound | Diagnostic read, mutation authority, impersonation, override, export, break-glass, approval, time box, and audit | Privileged human paths are separated for downstream gates | Compliance approval, production controls, or runbook execution is complete |
| Memory/graph/execution evidence is current | Prior claim source/date, current source reread, graph edge, command/report, exit code/status, and accepted/rejected decision | Old actor knowledge is reconciled with current evidence | Future edits, dynamic policy, or uninspected live provider state stay correct |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, previous role inventories, generated summaries, incidents, support notes, and execution output as selectors until current source, docs, tests, registry entries, policy files, or owner-controlled artifacts confirm them.
- Accept a prior "role exists", "support can access", "service account is scoped", "webhook is trusted", or "tenant boundary is enforced" claim only when current paths and fresh validation still match.
- Mark evidence stale after edits to role policy, route/job/webhook entry points, tenant scoping, support tooling, service accounts, integration contracts, generated clients, fixtures, reports, or validation commands.
- Record inspected and skipped boundaries: actor source, policy file, API route, UI route, job, webhook, service account, IdP/provider, support tool, audit event, test path, report artifact, and production-only control.
- Map every final role-confidence claim to a source path, command, report artifact, test, policy/doc section, owner review, or explicit not-verified residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source, registry, report, graph, and policy reads | Read-only local shell action; cite inspected paths and avoid full output dumps |
| Local validators, builds, reports, and dist/package generation | State-mutating only for reports, caches, dist/build/package artifacts, or temp files; cite command, exit code, artifact path, sandbox, and rollback |
| Connector, telemetry, production policy, IdP, IAM, or support-tool reads | External or secret-sensitive read; require owner, bounded scope, timestamp, redaction, and evidence-limit disclosure |
| Role policy, permission contract, source, test, or documentation updates | Local-write product action; record diff scope, rollback path, validation map, and downstream gate |

## Handoff Evidence Shape

```yaml
user_role_identification_evidence_closure:
  inspected_boundaries:
    - boundary: ""
      current_source_or_artifact: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
      freshness: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  role_to_validation_map:
    - actor_or_role: ""
      authority_boundary: ""
      data_visibility_boundary: ""
      source_path_or_artifact: ""
      validator_or_report: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_role_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```

## Blocking Conditions

Block closure when "user", "admin", "system", or "partner" remains a final actor type; actor authority lacks subject/resource/action/scope; data visibility omits hidden fields or exports; service accounts lack owner, scope, credential lifecycle, or audit; support/admin access merges diagnostic read with mutation or impersonation; external actors lack trusted/rejected claim boundaries; memory or graph evidence is reused without current-source confirmation; validation predates the final role edit; or state-mutating validation lacks permission/sandbox and rollback disclosure.
